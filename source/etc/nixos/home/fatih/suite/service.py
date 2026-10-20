"""User-session daemon: opt-in events, mount rules, history and inhibitors."""
import datetime as dt,json,os,signal,socket,stat,threading,time,traceback
from pathlib import Path
from common import CONFIG,STATE,RUNTIME,private,atomic,read,config,update,request,beneath
from productivity import Recorder,download_plan,apply_plan,outputs,monitor_rows,apply_monitors
from backend import APPS,History,Processes,mounts,network,notify,run,spawn,import_photos,eject,syncthing_status,signal_process

class Engine:
    def __init__(self):
        self.inhibitor=None;self.awake_until=0;self.awake_app='';self.presentation=False;self.private_hidden=False;self.history=History();self.processes=Processes();self.process_state={};self.mount_state=[];self.network='';self.initialized=False;self.old_apps=set();self.old_usb=set();self.old_network='';self.fired={};self.last_history=0;self.last_metrics=0;self.sync={};self.last_sync=0;self.stop_event=threading.Event();self.lock=threading.RLock();self.errors=[];self.recorder=Recorder();self.mute_until=0;self.last_download=0;self.last_monitors=0;self.output_names=None
    def error(self,e):
        self.errors=(self.errors+[{'time':time.time(),'text':str(e)[:400]}])[-10:];print(str(e),flush=True)
    def awake(self,minutes=0,app=''):
        self.cancel_awake();minutes=int(minutes)
        if minutes<=0 and not app:return 'Uyku engelleyicisi kapalı'
        if minutes<0 or minutes>1440 or len(app)>100:raise ValueError('Süre/uygulama geçersiz')
        if app and app not in self.process_state.get('apps',[]):raise ValueError('Seçilen uygulama çalışmıyor')
        self.awake_until=time.time()+minutes*60 if minutes else 0;self.awake_app=app
        try:request('qtile','global-awake',enabled=True)
        except (OSError,ValueError):pass
        self.inhibitor=spawn(['systemd-inhibit','--what=idle:sleep','--mode=block','--who=Violet','--why=Masaüstü odak / sunum','sleep','infinity'])
        return 'Uyku engelleyicisi etkin'
    def cancel_awake(self):
        if self.inhibitor and self.inhibitor.poll() is None:self.inhibitor.terminate()
        self.inhibitor=None;self.awake_until=0;self.awake_app=''
        try:request('qtile','global-awake',enabled=False)
        except (OSError,ValueError):pass
    def privacy(self,enabled):
        # IPC also closes private panels opened earlier. QML guards later openings.
        run(['qs','-c','fatih','ipc','call','desktop','privacy','true' if enabled else 'false'])
        self.private_hidden=enabled
    def present(self,enabled):
        enabled=bool(enabled)
        if enabled==self.presentation:return 'Sunum modu zaten '+('açık' if enabled else 'kapalı')
        if enabled:
            run(['makoctl','mode','-a','violet-presentation'])
            try:self.privacy(True);self.awake(120)
            except Exception:
                run(['makoctl','mode','-r','violet-presentation']);raise
        else:
            self.privacy(False);run(['makoctl','mode','-r','violet-presentation']);self.cancel_awake()
        self.presentation=enabled;atomic(STATE/'presentation.json',{'enabled':enabled});return 'Sunum modu '+('açık' if enabled else 'kapalı')
    def action(self,a):
        kind=a.get('kind')
        if kind=='app':
            name=a.get('app')
            if name not in APPS:raise ValueError('Uygulama listede yok')
            spawn(APPS[name]);return 'Uygulama açıldı'
        if kind=='preset':
            selected=next((p for p in config()['presets'] if p['id']==a.get('preset')),None)
            if not selected:raise ValueError('Kaydedilmiş düzen bulunamadı')
            return request('qtile','saved-preset',**{k:selected[k] for k in ('roles','template','group')})
        if kind=='notify':notify(str(a.get('text','Kural çalıştı'))[:400]);return 'Bildirim gönderildi'
        if kind=='awake':return self.awake(a.get('minutes',30))
        if kind=='presentation':return self.present(a.get('enabled',True))
        if kind=='mybrain':
            uuid=a.get('uuid');device=next((m for m in self.mount_state if m['uuid']==uuid and m['mounts']),None)
            if not device:raise ValueError('MyBrain USB bağlanmadı')
            relative=a.get('relative','MyBrain');root=Path(device['mounts'][0]);target=(root/relative).resolve()
            if not (target/'vault.json').is_file():target=(target/'data').resolve()
            if not beneath(target,root) or not (target/'vault.json').is_file():raise ValueError('USB içinde kasa bulunamadı')
            spawn(['mybrain-python','--vault',str(target)]);return 'MyBrain kasa ekranı açıldı'
        if kind=='photos':
            device=next((m for m in self.mount_state if m['uuid']==a.get('uuid') and m['mounts']),None)
            if not device:raise ValueError('Fotoğraf USB bağlı değil')
            root=Path(device['mounts'][0]);source=(root/a.get('relative','DCIM')).resolve()
            if not beneath(source,root):raise ValueError('USB kaynak yolu geçersiz')
            count=import_photos(source,a['destination']);notify(f'{count} fotoğraf/video kopyalandı');return f'{count} dosya kopyalandı'
        raise ValueError('Kural eylemi geçersiz')
    def rules(self,settings,now):
        apps=set(self.process_state.get('apps',[]));usb={m['uuid'] for m in self.mount_state if m['mounts'] and m['uuid']}
        date=dt.datetime.fromtimestamp(now);today=date.date().isoformat();clock=date.strftime('%H:%M')
        for rule in settings['rules']:
            if not rule.get('enabled',True):continue
            kind,value=rule.get('event'),rule.get('value');fire=False
            if kind=='usb':fire=self.initialized and value in usb-self.old_usb
            elif kind=='app':fire=self.initialized and value in apps-self.old_apps
            elif kind=='network':fire=self.initialized and self.network!=self.old_network and value==self.network
            elif kind=='time':fire=clock==value and self.fired.get(rule['id'])!=today
            if fire:
                self.fired[rule['id']]=today;atomic(STATE/'rule-fired.json',self.fired)
                try:self.action(rule['action'])
                except Exception as e:self.error(e);notify('Kural tamamlanamadı: '+str(e)[:160])
        if self.initialized and self.network!=self.old_network:
            for profile in settings['profiles']:
                if profile.get('uuid')==self.network:
                    try:
                        if profile.get('presentation') is not None:self.present(profile['presentation'])
                        if profile.get('preset'):self.action({'kind':'preset','preset':profile['preset']})
                        notify('Masaüstü profili: '+profile.get('name','Ağ profili'))
                    except Exception as e:self.error(e)
        self.old_apps=apps;self.old_usb=usb;self.old_network=self.network;self.initialized=True
    def mute(self,minutes):
        minutes=int(minutes)
        if not 0<=minutes<=1440:raise ValueError('Sessiz süresi 0–1440 dakika')
        run(['makoctl','mode','-a' if minutes else '-r','violet-timed'])
        self.mute_until=time.time()+minutes*60 if minutes else 0
        return 'Bildirim sessizi '+('açık' if minutes else 'kapalı')
    def productivity_tick(self,settings,now):
        self.recorder.tick()
        if self.mute_until and now>=self.mute_until:self.mute(0)
        if settings['downloadAuto'] and now-self.last_download>=60:
            self.last_download=now
            try:
                plan=download_plan(settings['downloadRoot'],settings['downloadRules'])
                if plan:notify(apply_plan(plan))
            except Exception as e:self.error(e)
        if now-self.last_monitors>=5:
            self.last_monitors=now
            try:
                connected=sorted(r['name'] for r in outputs())
                if self.output_names is not None and connected!=self.output_names:
                    profile=next((p for p in settings['monitorProfiles'] if p.get('auto') and sorted(r['name'] for r in p['rows'])==connected),None)
                    if profile:apply_monitors(profile['rows'],profile.get('groups'));notify('Monitör profili: '+profile['name'])
                self.output_names=connected
            except Exception as e:
                if settings['monitorProfiles']:self.error(e)
    def tick(self):
        with self.lock:
            now=time.time();settings=config()
            if now-self.last_metrics>=4:self.process_state=self.processes.sample();self.last_metrics=now
            self.mount_state=mounts();self.network=network()
            if self.inhibitor:
                if self.inhibitor.poll() is not None:self.error('Uyku engelleyicisi başlatılamadı/kapandı');self.cancel_awake()
                elif self.awake_until and now>=self.awake_until or self.awake_app and self.awake_app not in set(self.process_state.get('apps',[])):self.cancel_awake()
            if self.inhibitor:
                try:request('qtile','global-awake',enabled=True)
                except (OSError,ValueError):pass
            self.rules(settings,now);self.productivity_tick(settings,now)
            if settings['history'] and now-self.last_history>=300:
                try:self.history.scan()
                except Exception as e:self.error(e)
                self.last_history=now
            if now-self.last_sync>=20:self.sync=syncthing_status();self.last_sync=now
            atomic(STATE/'status.json',self.status())
    def status(self):return {'version':3,'recorder':self.recorder.status(),'mute_until':self.mute_until,'presentation':self.presentation,'private':self.private_hidden,'awake':bool(self.inhibitor and self.inhibitor.poll() is None),'awake_until':self.awake_until,'awake_app':self.awake_app,'mounts':self.mount_state,'network':self.network,'metrics':self.process_state,'sync':self.sync,'errors':self.errors}
    def dispatch(self,r):
        with self.lock:
            action=r.get('action')
            if action=='status':return self.status()
            if action=='awake':return self.awake(r.get('minutes',0),r.get('app',''))
            if action=='presentation':return self.present(not self.presentation if r.get('enabled') is None else r['enabled'])
            if action=='mute':return self.mute(r.get('minutes',0))
            if action=='record-start':return self.recorder.start(r['kind'],r.get('region',''),r.get('target',''),r.get('audio_source',''))
            if action=='record-stop':return self.recorder.stop()
            if action=='record-export':return self.recorder.export(r['seconds'],r['target'])
            if action=='eject':return eject(r['device'])
            if action=='history-scan':return self.history.scan()
            if action=='history-restore':return self.history.restore(r['ident'],r['stamp'],r['destination'])
            if action=='rule-test':return self.action(r['ruleAction'])
            if action=='signal':return signal_process(r['pid'],r['born'],r.get('kill',False))
            raise ValueError('Masaüstü işlemi geçersiz')

def main():
    root=private(RUNTIME);path=root/'suite.sock';engine=Engine();engine.fired=read(STATE/'rule-fired.json',{})
    if path.exists():
        try:request('suite','status');raise SystemExit('Violet servisi zaten çalışıyor')
        except (ConnectionRefusedError,FileNotFoundError):pass
        if not stat.S_ISSOCK(path.lstat().st_mode) or path.lstat().st_uid!=os.getuid():raise SystemExit('IPC yolu geçersiz')
        path.unlink()
    server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.bind(str(path));os.chmod(path,0o600);server.listen(8);server.settimeout(1)
    def loop():
        while not engine.stop_event.is_set():
            try:engine.tick()
            except Exception as e:engine.error(e)
            engine.stop_event.wait(2)
    def stop(*_):engine.stop_event.set()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    # On abnormal prior exit restore only this package's named notification mode.
    try:run(['makoctl','mode','-r','violet-presentation']);run(['makoctl','mode','-r','violet-timed'])
    except Exception:pass
    atomic(STATE/'presentation.json',{'enabled':False});worker=threading.Thread(target=loop,daemon=True);worker.start()
    try:
        while not engine.stop_event.is_set():
            try:conn,_=server.accept()
            except socket.timeout:continue
            with conn:
                conn.settimeout(2);raw=b''
                try:
                    while b'\n' not in raw:
                        data=conn.recv(4096)
                        if not data:raise ValueError('İstek eksik')
                        raw+=data
                        if len(raw)>65536:raise ValueError('İstek fazla büyük')
                    result={'ok':True,'data':engine.dispatch(json.loads(raw.split(b'\n',1)[0]))}
                except Exception as e:result={'ok':False,'error':str(e)}
                try:conn.sendall((json.dumps(result)+'\n').encode())
                except OSError:pass
    finally:
        engine.stop_event.set();worker.join(timeout=3);engine.cancel_awake();engine.recorder.stop();
        try:engine.mute(0)
        except Exception:pass
        atomic(STATE/'status.json',{'presentation':False,'awake':False})
        if engine.presentation:
            try:engine.present(False)
            except Exception:pass
        server.close();path.unlink(missing_ok=True)
if __name__=='__main__':main()
