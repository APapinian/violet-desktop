"""Desktop actions: argument vectors, explicit destinations and reversible file plans."""
import asyncio,configparser,datetime as dt,hashlib,json,os,re,shlex,shutil,signal,subprocess,tempfile,time,uuid,zipfile
from pathlib import Path
from common import CONFIG,STATE,RUNTIME,config,update,private,atomic,read,request,beneath
from backend import run,spawn
PAGES={'home':'Masaüstü','phone':'Telefon / S24+','notifications':'Bildirim merkezi','sessions':'Çalışma oturumları','downloads':'İndirilenler / adlandırma','ocr':'Ekrandan yazı','recording':'Ekran kaydı','audio':'Uygulama sesleri','apps':'Uygulamalar','storage':'Depolama bakımı','monitors':'Monitörler','settings':'Masaüstü ayarları'}

def apps():
    roots=[Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))]
    roots += [Path(x) for x in os.environ.get('XDG_DATA_DIRS','/run/current-system/sw/share:/etc/profiles/per-user/'+os.environ.get('USER','fatih')+'/share:/usr/local/share:/usr/share').split(':') if x]
    roots += [Path.home()/'.local/share/flatpak/exports/share',Path('/var/lib/flatpak/exports/share'),Path.home()/'.nix-profile/share']
    roots=list(dict.fromkeys(roots));found={}
    for root in roots:
        directory=root/'applications'
        if not directory.is_dir():continue
        for path in sorted(directory.rglob('*.desktop')):
            ident=str(path.relative_to(directory)).replace('/','-')
            if ident in found:continue
            found[ident]=None
            try:
                parser=configparser.ConfigParser(interpolation=None,strict=False);parser.read(path);d=parser['Desktop Entry']
                if d.get('Type','Application')!='Application' or d.get('Hidden','false').lower()=='true' or d.get('NoDisplay','false').lower()=='true':continue
                command=shlex.split(d['Exec']);argv=[]
                for arg in command:
                    if arg in ('%u','%U','%f','%F','%i'):continue
                    arg=arg.replace('%%','\0').replace('%c',d.get('Name',ident)).replace('%k',str(path))
                    if re.search('%[a-zA-Z]',arg):raise ValueError('Desteklenmeyen Exec alanı')
                    arg=arg.replace('\0','%').replace('\\$','$').replace('\\`','`')
                    argv.append(arg)
                if not argv:continue
                if d.get('Terminal','false').lower()=='true':argv=['foot','-e']+argv
                source='Flatpak' if d.get('X-Flatpak') else 'AppImage' if ident.startswith('appimage-') else 'Nix / masaüstü'
                found[ident]={'id':ident,'name':d.get('Name[tr]',d.get('Name',ident)),'icon':d.get('Icon','application-x-executable'),'argv':argv,'path':str(path),'classes':[d.get('StartupWMClass',argv[0].split('/')[-1]),ident[:-8]],'source':source}
            except (OSError,ValueError,KeyError,configparser.Error):continue
    return [x for x in found.values() if x]

def launch(ident):
    entry=next((x for x in apps() if x['id']==ident),None)
    if not entry:raise ValueError('Uygulama kaydı bulunamadı')
    spawn(entry['argv']);return 'Uygulama açıldı'

def walk(root,limit=30000):
    root=Path(root).expanduser().resolve();count=0
    if not root.is_dir():raise ValueError('Klasör bulunamadı')
    for current,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if not d.startswith('.') and d not in ('node_modules','target','__pycache__') and not (Path(current)/d).is_symlink()]
        for name in files:
            path=Path(current)/name
            if path.is_symlink():continue
            count+=1
            if count>limit:return
            try:
                if path.is_file():yield path,path.stat()
            except OSError:continue

def palette(query):
    q=query.casefold().strip();result=[]
    for a in apps():
        if not q or q in (a['name']+' '+a['id']).casefold():result.append({'label':a['name'],'detail':a['source'],'kind':'app','value':a['id']})
    for page,label in PAGES.items():
        if not q or q in label.casefold():result.append({'label':label,'detail':'Masaüstü ayarı','kind':'page','value':page})
    for c in config()['commands']:
        if not q or q in c['name'].casefold():result.append({'label':c['name'],'detail':'Kayıtlı komut','kind':'command','value':c['id']})
    if len(q)>=2:
        for root in config()['searchRoots']:
            if not Path(root).expanduser().is_dir():continue
            for p,_ in walk(root,8000):
                if q in p.name.casefold():result.append({'label':p.name,'detail':str(p.parent),'kind':'file','value':str(p)})
                if len(result)>=150:break
            if len(result)>=150:break
        try:
            for row in request('brain','search',query=q):result.append({'label':row['title'],'detail':'MyBrain · '+row['collection'],'kind':'brain','value':row})
        except (OSError,ValueError):pass
    return result[:200]

def activate(row):
    kind,value=row['kind'],row['value']
    if kind=='app':return launch(value)
    if kind=='file':spawn(['xdg-open',value])
    elif kind=='page':spawn(['violet-desktop',value])
    elif kind=='brain':return request('brain','open-record',collection=value['collection'],id=value['id'])
    elif kind=='command':
        record=next((c for c in config()['commands'] if c['id']==value),None)
        if not record:raise ValueError('Komut silinmiş')
        argv=record.get('argv');valid_argv(argv);spawn(argv)
    else:raise ValueError('Arama sonucu geçersiz')
    return 'Açıldı'

def valid_argv(argv):
    if not isinstance(argv,list) or not 0<len(argv)<=64 or any(not isinstance(x,str) or '\0' in x or len(x)>4096 for x in argv) or not argv[0]:raise ValueError('Komut bağımsız argümanlardan oluşmalı')
    return argv

async def _phones():
    from dbus_next.aio import MessageBus
    bus=await MessageBus().connect();name='org.kde.kdeconnect';root='/modules/kdeconnect'
    try:
        intro=await bus.introspect(name,root);daemon=bus.get_proxy_object(name,root,intro).get_interface('org.kde.kdeconnect.daemon');ids=await daemon.call_devices(False,False);out=[]
        for ident in ids:
            path=root+'/devices/'+ident;intro=await bus.introspect(name,path);props=bus.get_proxy_object(name,path,intro).get_interface('org.freedesktop.DBus.Properties');v=await props.call_get_all('org.kde.kdeconnect.device')
            out.append({'id':ident,'name':v['name'].value,'reachable':v['isReachable'].value,'paired':v['isPaired'].value,'type':v['type'].value})
        return out
    finally:bus.disconnect()
def phones():return asyncio.run(asyncio.wait_for(_phones(),timeout=8))
def phone(action,ident='',paths=None):
    if action=='refresh':return run(['kdeconnect-cli','--refresh'])
    devices=phones();selected=next((d for d in devices if d['id']==(ident or config()['phone'])),None)
    if not selected or not selected['reachable']:raise ValueError('Telefon erişilemiyor; aynı ağda KDE Connect’i aç')
    if action not in ('pair','ping','send-clipboard','share','ring'):raise ValueError('Telefon işlemi geçersiz')
    if action!='pair' and not selected['paired']:raise ValueError('Önce telefonda eşleşmeyi onayla')
    if action=='share':
        files=[str(regular(p)) for p in paths or []]
        if not files:raise ValueError('Gönderilecek dosya seç')
        for path in files:run(['kdeconnect-cli','--device',selected['id'],'--share',path])
        return f'{len(files)} dosya gönderildi'
    return run(['kdeconnect-cli','--device',selected['id'],'--'+action]) or 'Telefon işlemi gönderildi'

def notifications():
    out=[]
    for mode in ('list','history'):
        value=json.loads(run(['makoctl',mode,'-j']))
        # Current mako returns a JSON array; nested wrapper forms are also accepted.
        def collect(v):
            if isinstance(v,dict):
                if 'summary' in v:out.append({**v,'history':mode=='history'})
                else:
                    for child in v.values():collect(child)
            elif isinstance(v,list):
                for child in v:collect(child)
        collect(value)
    return out[:600]

def regular(path,max_size=None):
    path=Path(path).expanduser()
    if path.is_symlink() or not path.is_file():raise ValueError('Normal dosya gerekli: '+str(path))
    path=path.resolve()
    if max_size and path.stat().st_size>max_size:raise ValueError('Dosya çok büyük: '+path.name)
    return path

def fingerprint(p):
    s=p.stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]

def download_plan(root,rules=None,pattern=None):
    root=Path(root).expanduser().resolve();out=[]
    if not root.is_dir():raise ValueError('İndirilenler klasörü bulunamadı')
    for n,p in enumerate(sorted(root.iterdir()),1):
        if p.is_symlink() or not p.is_file() or p.name.endswith(('.part','.crdownload','.tmp')) or time.time()-p.stat().st_mtime<30:continue
        target=None
        if pattern is not None:
            try:name=pattern.format(name=p.stem,ext=p.suffix,n=n,date=dt.date.today().isoformat())
            except (ValueError,KeyError,IndexError):raise ValueError('Desen: {name}, {ext}, {n:03}, {date}')
            if name in ('','.','..') or Path(name).name!=name or '\0' in name:raise ValueError('Dosya adı deseni geçersiz')
            target=root/name
        else:
            for rule in rules if rules is not None else config()['downloadRules']:
                if p.suffix.lower().lstrip('.') in rule.get('extensions',[]):
                    folder=Path(rule['folder'])
                    if folder.is_absolute() or '..' in folder.parts:raise ValueError('Hedef İndirilenler içinde olmalı')
                    target=root/folder/p.name;break
        if target and target!=p:
            if not beneath(target.resolve(),root):raise ValueError('Hedef klasör dışına çıkıyor')
            out.append({'source':str(p),'target':str(target),'fingerprint':fingerprint(p)})
    return out

def apply_plan(plan,undo=False):
    if not isinstance(plan,list) or len(plan)>5000:raise ValueError('Dosya planı fazla büyük')
    targets=set();done=[]
    for row in plan:
        p=regular(row['source']);t=Path(row['target'])
        if fingerprint(p)!=row['fingerprint']:raise ValueError('Dosya değişti; önizlemeyi yenile: '+p.name)
        if t.exists() or t.is_symlink() or str(t) in targets:raise ValueError('Hedef zaten var / yineleniyor: '+str(t))
        if any(parent.is_symlink() for parent in t.parents):raise ValueError('Hedef symlink olamaz')
        targets.add(str(t))
    try:
        for row in plan:
            p=Path(row['source']);t=Path(row['target']);t.parent.mkdir(parents=True,exist_ok=True)
            if fingerprint(p)!=row['fingerprint']:raise ValueError('Dosya değişti')
            os.link(p,t,follow_symlinks=False)
            try:
                if fingerprint(p)!=row['fingerprint'] or fingerprint(t)!=row['fingerprint']:raise ValueError('Dosya taşıma sırasında değişti')
                p.unlink()
            except Exception:t.unlink();raise
            done.append({'source':str(t),'target':str(p),'fingerprint':fingerprint(t)})
    except Exception:
        for row in reversed(done):
            try:os.link(row['source'],row['target']);Path(row['source']).unlink()
            except OSError:pass
        raise
    if not undo:atomic(STATE/'downloads-undo.json',list(reversed(done)))
    return f'{len(done)} dosya '+('geri alındı' if undo else 'düzenlendi')

def undo_downloads():
    plan=read(STATE/'downloads-undo.json',[])
    if not plan:raise ValueError('Geri alınacak taşıma yok')
    result=apply_plan(plan,True);atomic(STATE/'downloads-undo.json',[]);return result

def ocr(region,language='tur+eng'):
    if language not in ('tur+eng','tur','eng'):raise ValueError('OCR dili geçersiz')
    shot=subprocess.run(['grim','-g',region,'-'],capture_output=True,timeout=10)
    if shot.returncode:raise ValueError(shot.stderr.decode(errors='replace'))
    text=subprocess.run(['tesseract','stdin','stdout','-l',language],input=shot.stdout,capture_output=True,timeout=60)
    if text.returncode:raise ValueError(text.stderr.decode(errors='replace')[:500])
    return text.stdout.decode(errors='replace')

def audio():return {'streams':json.loads(run(['pactl','-f','json','list','sink-inputs'])),'sinks':json.loads(run(['pactl','-f','json','list','sinks']))}
def audio_set(index,volume=None,sink=None,mute=None):
    current=audio()
    if index not in [s['index'] for s in current['streams']]:raise ValueError('Uygulamanın ses akışı kapandı')
    if volume is not None:
        if not 0<=int(volume)<=150:raise ValueError('Ses aralığı 0–150')
        run(['pactl','set-sink-input-volume',str(index),str(int(volume))+'%'])
    if mute is not None:run(['pactl','set-sink-input-mute',str(index),'1' if mute else '0'])
    if sink is not None:
        if sink not in [s['name'] for s in current['sinks']]:raise ValueError('Ses çıkışı kayboldu')
        run(['pactl','move-sink-input',str(index),sink])
    return 'Ses akışı güncellendi'

def flatpaks():
    value=run(['flatpak','list','--app','--columns=application,name,installation'])
    return [{'id':p[0],'name':p[1],'installation':p[2]} for line in value.splitlines() if len(p:=line.split('\t'))>=3]
def profile():
    value=json.loads(run(['nix','profile','list','--json']));entries=value.get('elements',{})
    return [{'id':str(k),'name':v.get('originalUrl') or v.get('originalUri') or str(k),'store':v.get('storePaths',[])} for k,v in (entries.items() if isinstance(entries,dict) else enumerate(entries))]
def appimages():
    root=Path.home()/'Applications';out=[]
    if root.is_dir():
        for p in root.iterdir():
            if p.is_symlink() or not p.is_file():continue
            try:
                with p.open('rb') as f:header=f.read(12)
                if header[:4]==b'\x7fELF' and header[8:10]==b'AI':out.append({'id':str(p),'name':p.name})
            except OSError:continue
    return out

def inventory():
    results={'desktop':apps(),'appimage':appimages(),'errors':[]}
    for key,fn in [('flatpak',flatpaks),('nix',profile)]:
        try:results[key]=fn()
        except Exception as e:results[key]=[];results['errors'].append(str(e))
    return results

def app_manage(kind,action,ident):
    if kind=='flatpak':
        if action=='install':
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]+',ident):raise ValueError('Flatpak uygulama kimliği geçersiz')
            argv=['flatpak','install','--user','--noninteractive','flathub',ident]
        else:
            if ident not in [a['id'] for a in flatpaks() if a['installation']=='user']:raise ValueError('Yalnız kullanıcı Flatpak uygulaması kaldırılabilir')
            argv=['flatpak','uninstall','--user','--noninteractive',ident]
    elif kind=='nix':
        if action=='install':
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*',ident):raise ValueError('Nix paket niteliği geçersiz')
            argv=['nix','profile','install','nixpkgs#'+ident]
        else:
            if ident not in [a['id'] for a in profile()]:raise ValueError('Kullanıcı Nix profilinde bulunamadı')
            argv=['nix','profile','remove',ident]
    elif kind=='appimage' and action=='remove':
        if ident not in [a['id'] for a in appimages()]:raise ValueError('Kayıtlı AppImage bulunamadı')
        root=Path.home()/'.local/share/applications';desktop=root/('appimage-'+hashlib.sha256(ident.encode()).hexdigest()[:12]+'.desktop')
        run(['gio','trash',ident])
        if desktop.exists():run(['gio','trash',str(desktop)])
        return 'AppImage çöp kutusuna taşındı'
    else:raise ValueError('Uygulama işlemi geçersiz')
    # Dedicated terminal shows progress and any errors; do not block the desktop daemon.
    spawn(['foot','-e']+argv);return 'İşlem terminalde başlatıldı; bittiğinde listeyi yenile'

def storage(root):
    values=list(walk(root,60000));sizes={};large=[]
    for p,s in values:
        large.append({'path':str(p),'size':s.st_size});sizes.setdefault(s.st_size,[]).append(p)
    duplicates=[]
    for size,paths in sizes.items():
        if not size or len(paths)<2:continue
        groups={}
        for p in paths:
            h=hashlib.sha256()
            try:
                with p.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                groups.setdefault(h.hexdigest(),[]).append(str(p))
            except OSError:continue
        duplicates.extend({'size':size,'paths':p} for p in groups.values() if len(p)>1)
    return {'large':sorted(large,key=lambda x:x['size'],reverse=True)[:300],'duplicates':duplicates[:300],'count':len(values),'limit':60000}
def generations():
    out=run(['nix-env','--list-generations','-p','/nix/var/nix/profiles/system']);return out

def outputs():return json.loads(run(['wlr-randr','--json']))
def monitor_rows(value):
    out=[]
    for d in value:
        current=next((m for m in d.get('modes',[]) if m.get('current')),None)
        mode=f"{current['width']}x{current['height']}@{current.get('refresh',60):g}Hz" if current else ''
        pos=d.get('position') or {};out.append({'name':d['name'],'enabled':d.get('enabled',False),'mode':mode,'scale':d.get('scale') or 1,'x':pos.get('x',0),'y':pos.get('y',0),'transform':d.get('transform') or 'normal'})
    return out

def monitor_args(rows,current):
    names={x['name'] for x in current};argv=['wlr-randr'];enabled=False;used=set()
    for row in rows:
        if row['name'] not in names or row['name'] in used:raise ValueError('Monitör bağlı değil / yineleniyor')
        used.add(row['name']);argv+=['--output',row['name'],'--on' if row['enabled'] else '--off']
        if row['enabled']:
            enabled=True;scale=float(row['scale']);x,y=int(row['x']),int(row['y'])
            if not .5<=scale<=4 or abs(x)>20000 or abs(y)>20000:raise ValueError('Ölçek veya konum geçersiz')
            if row.get('mode'):
                if not re.fullmatch(r'\d{2,5}x\d{2,5}(?:@\d+(?:\.\d+)?Hz)?',row['mode']):raise ValueError('Çözünürlük biçimi geçersiz')
                argv+=['--mode',row['mode']]
            transform=row.get('transform','normal')
            if transform not in ('normal','90','180','270','flipped','flipped-90','flipped-180','flipped-270'):raise ValueError('Ekran dönüşü geçersiz')
            argv+=['--scale',str(scale),'--pos',f'{x},{y}','--transform',transform]
    if used!=names or not enabled:raise ValueError('Tüm bağlı ekranları içeren ve en az bir açık ekranlı profil gerekli')
    return argv

def apply_monitors(rows,groups=None):
    before=monitor_rows(outputs());argv=monitor_args(rows,before)
    run(argv[:1]+['--dryrun']+argv[1:])
    try:run(argv)
    except Exception:
        try:run(monitor_args(before,before))
        except Exception:pass
        raise
    if groups:
        time.sleep(.8);request('qtile','screen-groups',groups=groups)
    return 'Monitör düzeni uygulandı'

def drop_files(paths,kind,destination='',device=''):
    if not 0<len(paths)<=200:raise ValueError('1–200 dosya bırak')
    files=[regular(p,128*1024*1024) for p in paths]
    if kind=='phone':return phone('share',device,[str(p) for p in files])
    if kind=='brain':return request('brain','attach',paths=[str(p) for p in files])
    folder=Path(destination).expanduser().resolve()
    if not folder.is_dir():raise ValueError('Hedef klasör seç')
    if kind=='zip':
        target=folder/('violet-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S')+'.zip')
        with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as z:
            names=set()
            for p in files:
                name=p.name
                if name in names:name=str(len(names))+'-'+name
                names.add(name);z.write(p,name)
        return str(target)
    if kind=='png':
        from PIL import Image
        for p in files:
            target=folder/(p.stem+'.png')
            if target==p:raise ValueError('Kaynak ve hedef aynı')
            with Image.open(p) as image, target.open('xb') as f:image.convert('RGBA').save(f,'PNG')
        return f'{len(files)} PNG oluşturuldu'
    raise ValueError('Dosya işlemi geçersiz')

def copy_new(source,target):
    fd,temporary=tempfile.mkstemp(prefix='.violet-',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as out,Path(source).open('rb') as inp:shutil.copyfileobj(inp,out);out.flush();os.fsync(out.fileno())
        os.link(temporary,target)
    finally:Path(temporary).unlink(missing_ok=True)

class Recorder:
    def __init__(self):self.process=None;self.encoder=None;self.kind='';self.directory=None;self.target=None;self.started=0;self.error=''
    def status(self):
        active=bool(self.process and self.process.poll() is None and (not self.encoder or self.encoder.poll() is None))
        return {'active':active,'kind':self.kind,'seconds':int(time.time()-self.started) if active else 0,'error':self.error}
    def start(self,kind,region='',target='',audio_source=''):
        if self.status()['active']:raise ValueError('Önce açık kaydı durdur')
        self.stop();self.error=''
        if kind not in ('record','replay'):raise ValueError('Kayıt türü geçersiz')
        if region and not re.fullmatch(r'-?\d+,-?\d+ \d+x\d+',region):raise ValueError('Alan geometrisi geçersiz')
        self.directory=Path(tempfile.mkdtemp(prefix='replay-',dir=private(RUNTIME)));self.kind=kind;self.started=time.time()
        argv=['wf-recorder','-y','-r','30','-D','-c','libx264','-p','preset=veryfast','-p','crf=23','-p','g=150','-x','yuv420p']
        if region:argv+=['-g',region]
        if audio_source:argv+=['--audio='+audio_source]
        self.log=(self.directory/'capture.log').open('wb')
        if kind=='record':
            self.target=Path(target).expanduser().resolve()
            if self.target.suffix!='.mkv' or not self.target.parent.is_dir() or self.target.exists():self.stop();raise ValueError('Yeni bir .mkv kayıt yolu seç')
            self.process=subprocess.Popen(argv+['-f',str(self.directory/'record.mkv')],stdout=subprocess.DEVNULL,stderr=self.log)
        else:
            self.process=subprocess.Popen(argv+['-m','matroska','-f','/dev/stdout'],stdout=subprocess.PIPE,stderr=self.log)
            self.encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-i','pipe:0','-c','copy','-f','segment','-segment_time','5','-reset_timestamps','1',str(self.directory/'segment-%06d.mkv')],stdin=self.process.stdout,stdout=subprocess.DEVNULL,stderr=self.log)
            self.process.stdout.close()
        return 'Kayıt başladı' if kind=='record' else 'Tekrar tamponu başladı'
    def tick(self):
        if self.kind and not self.status()['active']:
            if self.directory:self.error=(self.directory/'capture.log').read_text(errors='replace')[-600:]
            self.stop();return
        if self.kind=='replay':
            files=sorted(self.directory.glob('segment-*.mkv'))
            for p in files[:-19]:p.unlink(missing_ok=True)
            if sum(p.stat().st_size for p in files if p.exists())>1024**3:self.error='Tampon 1 GiB sınırına ulaştı';self.stop()
    def export(self,seconds,target):
        if self.kind!='replay' or not self.status()['active']:raise ValueError('Tekrar tamponu açık değil')
        seconds=int(seconds)
        if seconds not in (30,60):raise ValueError('30 veya 60 saniye seç')
        files=sorted(self.directory.glob('segment-*.mkv'))[:-1][-seconds//5:]
        if not files:raise ValueError('İlk 5 saniyelik parça henüz tamamlanmadı')
        dest=Path(target).expanduser().resolve()
        if dest.suffix!='.mkv' or dest.exists() or not dest.parent.is_dir():raise ValueError('Yeni .mkv dosyası seç')
        # Snapshot closed segments so retention cannot invalidate the concat input.
        snap=Path(tempfile.mkdtemp(prefix='export-',dir=self.directory))
        try:
            names=[]
            for i,p in enumerate(files):name=f'{i}.mkv';os.link(p,snap/name);names.append(name)
            (snap/'list.txt').write_text(''.join("file '"+n+"'\n" for n in names))
            out=snap/'out.mkv';r=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','concat','-safe','1','-i',str(snap/'list.txt'),'-c','copy',str(out)],capture_output=True,timeout=60)
            if r.returncode:raise ValueError(r.stderr.decode(errors='replace')[:400])
            copy_new(out,dest)
            return f'{len(files)*5} saniye kaydedildi · son açık parça (0–5 sn) hariç'
        finally:shutil.rmtree(snap)
    def stop(self):
        was=self.kind;directory=self.directory;target=self.target
        for p in (self.process,self.encoder):
            if p and p.poll() is None:
                p.send_signal(signal.SIGINT)
                try:p.wait(timeout=4)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
        if getattr(self,'log',None):self.log.close();self.log=None
        result='Kayıt durduruldu'
        if was=='record' and directory and target and (directory/'record.mkv').exists():
            source=directory/'record.mkv'
            if source.stat().st_size:
                if target.exists():target=target.with_name(target.stem+'-kurtarilan-'+uuid.uuid4().hex[:8]+'.mkv')
                copy_new(source,target);result=str(target)
        if directory:shutil.rmtree(directory,ignore_errors=True)
        self.process=self.encoder=None;self.kind='';self.directory=self.target=None;return result
