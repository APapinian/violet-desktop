#!/usr/bin/env python3
"""One user daemon; local UNIX IPC; bounded provider polling outside the UI."""
import argparse
import ast
import asyncio
import concurrent.futures
import datetime as dt
import json
import math
import operator
import os
import re
import socket
import subprocess
import sys
import time
import threading
import signal
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlencode
from common import CONFIG, STATE, RUNTIME, Store, NeedsConfig, atomic, load, settings, validate_settings, run, detach, get_json, safe_url
from providers import PROVIDERS

SOCKET=RUNTIME/'service.sock'
MPV_SOCKET=RUNTIME/'mpv.sock'


def mpv(command):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(3);s.connect(str(MPV_SOCKET));s.sendall((json.dumps({'command':command,'request_id':1})+'\n').encode())
        with s.makefile() as f:
            for line in f:
                data=json.loads(line)
                if data.get('request_id')==1:
                    if data.get('error')!='success':raise RuntimeError('mpv: '+str(data.get('error')))
                    return data.get('data')


def calc(expression):
    if len(expression)>256:raise ValueError('İfade çok uzun')
    ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod,ast.Pow:operator.pow}
    tree=ast.parse(expression,mode='eval')
    if len(list(ast.walk(tree)))>100:raise ValueError('İfade sınırı')
    def value(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):v=n.value
        elif isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):v=value(n.operand)*(1 if isinstance(n.op,ast.UAdd) else -1)
        elif isinstance(n,ast.BinOp) and type(n.op) in ops:
            a,b=value(n.left),value(n.right)
            if isinstance(n.op,ast.Pow) and abs(b)>16:raise ValueError('Üs en fazla 16')
            v=ops[type(n.op)](a,b)
        else:raise ValueError('Yalnızca sayısal aritmetik')
        if not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1e100:raise ValueError('Sonuç sınırı')
        return v
    return str(value(tree.body))


def parse_lrc(text):
    result=[]
    for line in text.splitlines():
        times=re.findall(r'\[(\d+):(\d+(?:\.\d+)?)\]',line)
        words=re.sub(r'\[[^]]*\]','',line).strip()
        for minute,second in times:result.append(dict(time=int(minute)*60+float(second),text=words))
    return sorted(result,key=lambda x:x['time'])


class Kingdom:
    def __init__(self):
        self.action_pool=concurrent.futures.ThreadPoolExecutor(max_workers=2,thread_name_prefix='kingdom-action')
        self.lock=threading.RLock();self.store=Store();self.due={};self.pending={};self.config=settings();self.last_config=0
        self.local=load(STATE/'local.json',{'pomodoro':{},'queue':[],'later':[],'notes':'','usage':{},'tasks':[]})
        self.notifications={};self.net_previous=None;self.net_time=0;self.network={};self.game=False;self.last_game=None
        self.lyric_key='';self.lyrics=[];self.lyric_status='Henüz bir şarkı yok';self.last_lyric_request=0
        self.last_focus=None;self.focus_time=time.monotonic();self.usage_session=load(Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/'fatih-qtile.json').get('session')

    def save(self):
        with self.lock:atomic(STATE/'local.json',self.local)

    def notify(self,key,title,body,interval=1800):
        if self.game or time.time()-self.notifications.get(key,0)<interval:return
        self.notifications[key]=time.time()
        detach(['notify-send','--app-name=Krallık','--',title,body])

    async def poll(self,name,fn):
        try:
            data=await asyncio.to_thread(fn,self.config,self.store)
            self.store.put(name,data)
            if name=='feeds' and self.config['alerts']['rss']:
                for source in data['sources']:
                    if source.get('new'):self.notify('rss:'+source['id'],source['name'],str(len(source['new']))+' yeni içerik',900)
            if name=='earthquakes':
                for e in data['items']:
                    if e['magnitude']>=self.config['alerts']['earthquake']:
                        try:recent=dt.datetime.fromisoformat(e['time']).replace(tzinfo=dt.timezone.utc).timestamp()>time.time()-900
                        except (ValueError,TypeError):recent=False
                        if recent:self.notify('quake:'+str(e['id']),'AFAD deprem kaydı',str(e['magnitude'])+' · '+e['title'],86400)
        except NeedsConfig as e:self.store.put(name,None,'configuration_required',str(e))
        except Exception as e:
            # Avoid including URL tokens, mail addresses or authorization values in logs/UI.
            code=getattr(getattr(e,'response',None),'status_code',None)
            self.store.put(name,None,'error',type(e).__name__+((' HTTP '+str(code)) if code else ''))

    def network_tick(self):
        now=time.monotonic();values={}
        for d in Path('/sys/class/net').glob('*'):
            if d.name=='lo':continue
            try:values[d.name]=(int((d/'statistics/rx_bytes').read_text()),int((d/'statistics/tx_bytes').read_text()))
            except OSError:pass
        if self.net_previous and now>self.net_time:
            dtm=now-self.net_time
            self.network={k:dict(down=max(0,(v[0]-self.net_previous.get(k,v)[0])/dtm),up=max(0,(v[1]-self.net_previous.get(k,v)[1])/dtm)) for k,v in values.items()}
        self.net_previous,self.net_time=values,now

    def time_tick(self):
        p=self.local.get('pomodoro',{})
        if p.get('running') and p['deadline']<=time.time():
            p.update(running=False,remaining=0)
            self.notify('pomodoro','Pomodoro tamamlandı','Mola zamanı' if p.get('mode')=='work' else 'Çalışmaya dön',1);self.save()
        if self.config['alerts']['hourlyBreak']:
            hour=int(time.time()//3600)
            if getattr(self,'break_hour',None) is None:self.break_hour=hour
            elif self.break_hour!=hour:
                self.break_hour=hour;self.notify('break','Kısa mola','Ayağa kalk, gözlerini dinlendir.',3000)
        hw=self.store.get('hardware').get('data') or {}
        if self.store.get('hardware')['status']=='ready':
            for b in hw.get('batteries',[]):
                if b['percent'] is not None and b['percent']<=self.config['alerts']['battery'] and b['status']=='Discharging':self.notify('battery','Pil azalıyor',str(b['percent'])+'%')
            if any(t['value']>=self.config['alerts']['temperature'] for t in hw.get('temperatures',[])):self.notify('hot','Yüksek sıcaklık','Sistem sıcaklık panelini kontrol et.')
            for d in hw.get('disks',[]):
                if d['percent']>=90:self.notify('disk:'+d['path'],'Disk doluluk uyarısı',d['path']+' · %'+str(round(d['percent'])))
        events=(self.store.get('calendar').get('data') or {}).get('items',[])
        for e in events:
            if 0<e['timestamp']-time.time()<=self.config['calendar']['reminder_minutes']*60:self.notify('calendar:'+e['id'],e['title'],e['time'],86400)

    def usage_tick(self):
        bridge=load(Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/'fatih-kingdom-qtile.json');now=time.monotonic()
        name=bridge.get('application')
        if self.config['usageTracking'] and name and self.last_focus:
            date=dt.date.today().isoformat();day=self.local.setdefault('usage',{}).setdefault(date,{})
            day[self.last_focus]=day.get(self.last_focus,0)+min(5,now-self.focus_time)
        self.last_focus=name;self.focus_time=now
        self.game=bool(bridge.get('game'))
        if self.game!=self.last_game:
            # Named mode leaves the user's other notification modes untouched.
            try:run(['makoctl','mode','-a' if self.game else '-r','kingdom-gaming'])
            except Exception:pass
            self.last_game=self.game

    async def lyric_fetch(self,key,title,artist):
        try:
            output=await asyncio.to_thread(run,[sys.executable,str(Path(__file__).with_name('lyrics.py')),title+' '+artist],40)
            self.lyrics=parse_lrc(json.loads(output)['lyrics']);self.lyric_status='Hazır' if self.lyrics else 'Senkron söz bulunamadı'
        except Exception:self.lyrics=[];self.lyric_status='Senkron söz alınamadı'
        self.lyric_key=key

    async def ticker(self):
        while True:
            now=time.monotonic()
            if now-self.last_config>10:self.config=settings();self.last_config=now
            for name,(ttl,fn) in PROVIDERS.items():
                if name in self.pending and self.pending[name].done():self.pending.pop(name)
                if name not in self.pending and now>=self.due.get(name,0):
                    self.pending[name]=asyncio.create_task(self.poll(name,fn));self.due[name]=now+ttl
            with self.lock:
                self.network_tick();self.usage_tick();self.time_tick()
            m=(self.store.get('media').get('data') or {}).get('current')
            key=(m['title']+'\0'+m['artist']) if m else ''
            if key and key!=self.lyric_key and (not getattr(self,'lyric_task',None) or self.lyric_task.done()):
                self.lyric_key=key;self.lyrics=[];self.lyric_status='Söz aranıyor'
                self.lyric_task=asyncio.create_task(self.lyric_fetch(key,m['title'],m['artist']))
            snapshot=self.snapshot();atomic(RUNTIME/'state.json',snapshot)
            if int(time.time())%30==0:self.save()
            await asyncio.sleep(1)

    def snapshot(self):
        with self.lock:return self._snapshot()

    def _snapshot(self):
        data=self.store.all();m=(data.get('media',{}).get('data') or {}).get('current');line=''
        if m and self.lyrics:
            pos=m['position']+(time.time()-data['media']['updated'] if m['status']=='Playing' else 0)
            for e in self.lyrics:
                if e['time']>pos:break
                line=e['text']
        p=dict(self.local.get('pomodoro',{}))
        if p.get('running'):p['remaining']=max(0,int(p['deadline']-time.time()))
        physical=load('/run/yoga-tablet/state.json',{'tablet':False,'available':False})
        tablet=dict(physical,settings=self.config['tablet'],override=self.local.get('tabletOverride'))
        tablet['sensor']=load(RUNTIME/'orientation.json',dict(available=False))
        schedule=self.config['themeSchedule'];wallpaper='';day=False
        if schedule.get('enabled'):
            clock=dt.datetime.now().strftime('%H:%M');day=schedule['day']<=clock<schedule['night']
            candidate=Path(schedule.get('dayWallpaper' if day else 'nightWallpaper','')).expanduser()
            if candidate.is_file():wallpaper=candidate.as_uri()
        news=[e for source in (data.get('feeds',{}).get('data') or {}).get('sources',[]) if source['kind']=='news' for e in source['items']]
        next_items=(data.get('queue',{}).get('data') or {}).get('upcoming',[])
        return dict(version=1,now=time.time(),providers=data,network=self.network,pomodoro=p,tablet=tablet,game=self.game,
                    wallpaper=wallpaper,day=day,scheduled=bool(schedule.get('enabled')),headlines=news,upcoming=next_items,
                    lyrics=dict(line=line,status=self.lyric_status),queue=self.local.get('queue',[]),later=self.local.get('later',[]),
                    notes=self.local.get('notes',''),tasks=self.local.get('tasks',[])+[dict(e,done=self.local.get('taskDone',{}).get(e['id'],e.get('done',False))) for e in self.config.get('tasks',[])],goals=self.config.get('goals',[]),
                    usage=self.local.get('usage',{}),location=self.config['location']['name'],commands=self.config['commands'],radios=self.config['radios'])

    def start_mpv(self):
        try:mpv(['get_property','idle-active']);return
        except Exception:pass
        detach(['mpv','--idle=yes','--no-terminal','--force-window=no','--input-ipc-server='+str(MPV_SOCKET)])
        for _ in range(50):
            try:mpv(['get_property','idle-active']);return
            except Exception:time.sleep(.05)
        raise RuntimeError('mpv başlatılamadı')

    def play(self,item,append=False,video=False):
        url=safe_url(item['url']);self.start_mpv()
        mpv(['set_property','vid','auto' if video else 'no'])
        mpv(['loadfile',url,'append-play' if append else 'replace'])
        with self.lock:
            queue=self.local.setdefault('queue',[])
            if not append:queue.clear()
            queue.append({**item,'duration':item.get('duration',0)})
            self.save()

    def action(self,request):
        if request.get("action") in {"notes-save","task-add","task-toggle","pomodoro","tablet","later-add","later-remove"}:
            with self.lock:return self._action(request)
        return self._action(request)

    def _action(self,request):
        action=request.get('action');value=request.get('value');c=self.config
        if action=='snapshot':return self.snapshot()
        if action=='refresh':
            if value not in PROVIDERS:raise ValueError('Sağlayıcı adı gerekli')
            # UI refresh is rate limited and does not bypass cached account/API polls.
            last=self.store.get(value)['updated'];delay=max(5,30-(time.time()-last))
            self.due[value]=min(self.due.get(value,0),time.monotonic()+delay);return 'Yenileme sıraya alındı'
        if action=='settings':return settings()
        if action=='settings-save':
            validate_settings(value)
            atomic(CONFIG/'settings.json',value);self.config=settings();self.due={};return 'Ayarlar kaydedildi'
        if action=='geocode':
            return get_json('https://geocoding-api.open-meteo.com/v1/search?'+urlencode(dict(name=str(value),count=8,language='tr',format='json'))).get('results',[])
        if action=='location':
            s=load(CONFIG/'settings.json',{'version':1});s['location']=value;s['version']=1;validate_settings(s);atomic(CONFIG/'settings.json',s);self.config=settings();self.due.update(weather=0,prayer=0,aqi=0);return value
        if action=='mark-feed':
            self.store.mark(str(value));r=self.store.get('feeds')
            if r['data']:
                for row in r['data']['sources']:
                    if row['id']==value:row['count']=0;row['new']=[]
                self.store.put('feeds',r['data'])
            return 'Okundu'
        # VIOLET_LOCAL_MUSIC_V1
        if action=='play-local':
            if not isinstance(value,list) or not value or len(value)>200:raise ValueError('Yerel müzik listesi geçersiz')
            paths=[Path(x).expanduser().resolve() for x in value if isinstance(x,str)]
            if len(paths)!=len(value) or not all(p.is_file() for p in paths):raise ValueError('Müzik dosyası bulunamadı')
            self.start_mpv()
            for index,path in enumerate(paths):
                mpv(['loadfile',str(path),'replace' if index==0 else 'append-play'])
            with self.lock:
                self.local['queue']=[dict(url=str(p),title=p.stem) for p in paths]
                self.save()
            return 'Yerel müzik açıldı'
        if action=='search-music':
            from ytmusicapi import YTMusic
            rows=YTMusic().search(str(value),filter='songs',limit=20)
            return [dict(title=e['title'],artist=', '.join(x['name'] for x in e.get('artists',[])),url='https://www.youtube.com/watch?v='+e['videoId'],duration=e.get('duration_seconds',0),art=(e.get('thumbnails') or [{}])[-1].get('url','')) for e in rows if e.get('videoId')]
        if action=='search-video':
            out=run(['yt-dlp','--flat-playlist','--dump-single-json','--no-warnings','--socket-timeout','10','--','ytsearch10:'+str(value)],45)
            return [dict(title=e['title'],url=e.get('webpage_url') or 'https://www.youtube.com/watch?v='+e['id'],duration=e.get('duration',0)) for e in json.loads(out)['entries'] if e]
        if action in ('play','enqueue','play-video'):
            self.play(value,append=action=='enqueue',video=action=='play-video');return 'Oynatıcıya gönderildi'
        if action=='later-add':
            safe_url(value['url']);self.local.setdefault('later',[]).append(value);self.save();return 'Daha sonra izle listesine eklendi'
        if action=='later-remove':self.local['later']=[e for e in self.local.get('later',[]) if e['url']!=value];self.save();return 'Listeden çıkarıldı'
        if action=='queue':
            try:return dict(playlist=mpv(['get_property','playlist']),items=self.local.get('queue',[]))
            except Exception:return dict(playlist=[],items=self.local.get('queue',[]))
        if action=='mpv':
            if value not in ('playlist-next','playlist-prev','pause','stop'):raise ValueError('Oynatıcı komutu')
            return mpv(['cycle','pause'] if value=='pause' else [value])
        if action=='player':
            if value.get('command') not in ('play-pause','next','previous','stop'):raise ValueError('MPRIS komutu')
            return run(['playerctl','-p',value['player'],value['command']])
        if action=='radio-search':
            return get_json('https://de1.api.radio-browser.info/json/stations/search?'+urlencode(dict(countrycode='TR',name=str(value),hidebroken='true',limit=30,order='votes',reverse='true')))
        if action=='notes-save':self.local['notes']=str(value)[:200000];self.save();return 'Not kaydedildi'
        if action=='task-add':self.local.setdefault('tasks',[]).append(dict(id=str(time.time_ns()),text=str(value)[:500],done=False));self.save();return 'Görev eklendi'
        if action=='task-toggle':
            for task in self.local.get('tasks',[]):
                if task['id']==value:task['done']=not task['done'];self.save();return 'Görev güncellendi'
            for task in self.config.get('tasks',[]):
                if task['id']==value:
                    done=self.local.setdefault('taskDone',{});done[value]=not done.get(value,task.get('done',False))
            self.save();return 'Görev güncellendi'
        if action=='calculate':return calc(str(value))
        if action=='pomodoro':
            p=self.local.setdefault('pomodoro',{})
            if value in ('work','break'):p.update(mode=value,running=True,deadline=time.time()+(1500 if value=='work' else 300),remaining=1500 if value=='work' else 300)
            elif value=='pause':p.update(remaining=max(0,int(p.get('deadline',time.time())-time.time())),running=False)
            elif value=='resume':p.update(deadline=time.time()+p.get('remaining',1500),running=True)
            elif value=='reset':p.update(running=False,remaining=1500,mode='work')
            else:raise ValueError('Pomodoro komutu')
            self.save();return 'Sayaç güncellendi'
        if action=='clipboard':
            text=run(['cliphist','list']);return [dict(id=row.split('\t',1)[0],text=row.split('\t',1)[-1]) for row in text.splitlines()[:100]]
        if action=='clipboard-copy':
            data=subprocess.run(['cliphist','decode'],input=str(value).encode(),capture_output=True,timeout=5,check=True).stdout
            subprocess.run(['wl-copy'],input=data,check=True,timeout=5);return 'Panoya alındı'
        if action=='copy':run(['wl-copy'],input=str(value));return 'Kopyalandı'
        if action=='screenshot':
            directory=Path.home()/'Resimler/EkranGoruntuleri';directory.mkdir(parents=True,exist_ok=True);target=directory/(str(time.time_ns())+'.png')
            args=['grim']
            if value=='area':args+=['-g',run(['slurp'],timeout=120)]
            elif value=='window':
                geo=load(Path(os.environ['XDG_RUNTIME_DIR'])/'fatih-kingdom-qtile.json').get('geometry')
                if not geo:raise ValueError('Aktif pencere geometrisi yok')
                args+=['-g',f"{geo['x']},{geo['y']} {geo['width']}x{geo['height']}"]
            elif value!='screen':raise ValueError('Ekran görüntüsü türü')
            run(args+[str(target)],timeout=10);self.notify('shot','Ekran görüntüsü kaydedildi',str(target),1);return str(target)
        if action=='audio-sinks':
            import pulsectl
            with pulsectl.Pulse('fatih-kingdom') as p:
                default=p.server_info().default_sink_name
                return [dict(name=s.name,description=s.description,index=s.index,default=s.name==default) for s in p.sink_list()]
        if action=='audio-sink':
            import pulsectl
            with pulsectl.Pulse('fatih-kingdom') as p:
                sink=next(s for s in p.sink_list() if s.name==value);p.default_set(sink)
                for stream in p.sink_input_list():p.sink_input_move(stream.index,sink.index)
            return 'Ses çıkışı değişti'
        if action=='volume':
            import pulsectl
            with pulsectl.Pulse('fatih-kingdom') as p:
                sink=next(s for s in p.sink_list() if s.name==p.server_info().default_sink_name);p.volume_set_all_chans(sink,max(0,min(1,float(value))))
            return 'Ses seviyesi değişti'
        if action=='power':
            cmds={'lock':['swaylock','--color','17151f'],'suspend':['systemctl','suspend'],'reboot':['systemctl','reboot'],'off':['systemctl','poweroff']}
            if value not in cmds:raise ValueError('Güç komutu')
            detach(cmds[value]);return 'Komut gönderildi'
        if action=='connectivity':
            cmds={'wifi':['foot','-e','nmtui'],'bluetooth':['blueman-manager']}
            detach(cmds[value]);return 'Bağlantı menüsü açıldı'
        if action=='translation':
            command=c['translation']['command']
            if not command:raise NeedsConfig('LinguaMap başlatma komutunu ayarlara ekle')
            detach(command);return 'Çeviri açıldı'
        if action=='saved-command':
            row=next(e for e in c['commands'] if e['id']==value)
            if not isinstance(row['argv'],list) or not all(isinstance(x,str) for x in row['argv']):raise ValueError('argv dizisi gerekli')
            detach(row['argv']);return 'Komut başlatıldı'
        if action=='open-url':detach(['xdg-open',safe_url(value)]);return 'Açıldı'
        if action=='tablet':
            if value not in ('auto','on','off','keyboard-toggle','rotation-toggle'):raise ValueError('Tablet komutu')
            if value in ('auto','on','off'):self.local['tabletOverride']=None if value=='auto' else value=='on';self.save()
            else:
                s=load(CONFIG/'settings.json',{'version':1});t=s.setdefault('tablet',dict(self.config['tablet']));k='keyboard' if value=='keyboard-toggle' else 'rotation';t[k]=not t[k];atomic(CONFIG/'settings.json',s);self.config=settings()
            return 'Tablet tercihi kaydedildi'
        raise ValueError('Bilinmeyen eylem: '+str(action))

    async def handle(self,reader,writer):
        try:
            request=json.loads(await asyncio.wait_for(reader.readline(),timeout=10))
            if request.get('action')=='watch':
                last=''
                while not writer.is_closing():
                    line=json.dumps(self.snapshot(),ensure_ascii=False)
                    if line!=last:writer.write((line+'\n').encode());await writer.drain();last=line
                    await asyncio.sleep(1)
            else:
                try:response=dict(ok=True,result=await asyncio.get_running_loop().run_in_executor(self.action_pool,self.action,request))
                except (NeedsConfig,ValueError) as e:response=dict(ok=False,error=str(e))
                except Exception as e:response=dict(ok=False,error=type(e).__name__)
                writer.write((json.dumps(response,ensure_ascii=False)+'\n').encode());await writer.drain()
        except (ConnectionError,asyncio.TimeoutError,ValueError):pass
        finally:writer.close()


async def serve():
    pool=concurrent.futures.ThreadPoolExecutor(max_workers=6);asyncio.get_running_loop().set_default_executor(pool)
    if SOCKET.exists():SOCKET.unlink()
    app=Kingdom();server=await asyncio.start_unix_server(app.handle,path=SOCKET,limit=300000);SOCKET.chmod(0o600)
    task=asyncio.create_task(app.ticker())
    from sensors import watch as watch_sensors
    sensor_task=asyncio.create_task(watch_sensors())
    stop=asyncio.Event();asyncio.get_running_loop().add_signal_handler(signal.SIGTERM,stop.set)
    task.add_done_callback(lambda completed:stop.set())
    try:
        async with server:await stop.wait()
        if task.done() and not task.cancelled() and task.exception():raise task.exception()
    finally:
        task.cancel();sensor_task.cancel()
        with suppress(asyncio.CancelledError):await sensor_task
        app.save()
        app.action_pool.shutdown(wait=False,cancel_futures=True)
        if app.last_game:
            try:run(['makoctl','mode','-r','kingdom-gaming'])
            except Exception:pass
        SOCKET.unlink(missing_ok=True)


def client(action,value=None):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(130 if action=='screenshot' else 65);s.connect(str(SOCKET));s.sendall((json.dumps(dict(action=action,value=value))+'\n').encode())
        with s.makefile() as f:
            if action=='watch':
                for line in f:print(line,end='',flush=True)
            else:
                line=f.readline();print(line,end='',flush=True)
                if not json.loads(line).get('ok'):raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',nargs='?',default='snapshot');parser.add_argument('value',nargs='?');args=parser.parse_args()
    try:
        if args.action=='serve':asyncio.run(serve())
        else:client(args.action,json.loads(args.value) if args.value is not None else None)
    except (KeyboardInterrupt,BrokenPipeError):pass
    except (FileNotFoundError,ConnectionRefusedError):print(json.dumps(dict(ok=False,error='Krallık servisi çalışmıyor; systemctl --user start fatih-kingdom.service')));sys.exit(1)
