"""Desktop operations: selected folders only, real process and mount data."""
import datetime as dt,hashlib,json,os,re,shutil,subprocess,tempfile,time,zipfile,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
import psutil
from common import CONFIG,STATE,RUNTIME,atomic,private,read,config,update,request,beneath
APPS={'Dosyalar':['nautilus'],'MyBrain':['mybrain-python'],'Tarayıcı':['firefox'],'Terminal':['kitty'],'Metin':['gnome-text-editor'],'PDF':['papers'],'Buds':['GalaxyBudsClient'],'Senkronizasyon':['xdg-open','http://127.0.0.1:8384']}

def run(args,timeout=12):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    if p.returncode:raise ValueError((p.stderr or p.stdout or 'Komut başarısız').strip()[:600])
    return p.stdout

def spawn(args):
    return subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)

def notify(message):
    try:spawn(['notify-send','Violet',message])
    except OSError:pass

def mounts():
    data=json.loads(run(['lsblk','--json','--paths','--output','NAME,TYPE,TRAN,RM,UUID,LABEL,MOUNTPOINTS,PKNAME']))
    result=[]
    def walk(node,device=None,usb=False):
        usb=usb or node.get('tran')=='usb' or bool(node.get('rm'))
        device=node['name'] if node.get('type')=='disk' else device
        if usb:
            points=[str(Path(x).resolve()) for x in (node.get('mountpoints') or []) if x]
            result.append({'name':node['name'],'disk':device or node['name'],'type':node.get('type'),'uuid':node.get('uuid') or '', 'label':node.get('label') or Path(node['name']).name,'mounts':points})
        for child in node.get('children',[]):walk(child,device,usb)
    for node in data.get('blockdevices',[]):walk(node)
    return result

def users_of(points):
    roots=[Path(p).resolve() for p in points];result=[];limited=False
    for p in psutil.process_iter(['pid','name','username']):
        try:
            if p.uids().real!=os.getuid():continue
            hits=[x.path for x in p.open_files() if any(beneath(Path(x.path).resolve(),root) for root in roots)]
            cwd=p.cwd()
            if any(beneath(Path(cwd).resolve(),root) for root in roots):hits.append('Çalışma dizini: '+cwd)
            if hits:result.append({'pid':p.pid,'name':p.name(),'files':hits[:12]})
        except (psutil.AccessDenied,psutil.NoSuchProcess):limited=True
    try:
        brain=request('brain','status')
        if brain.get('root') and any(beneath(Path(brain['root']),root) for root in roots):result.append({'pid':brain['pid'],'name':'MyBrain · açık kasa','files':[brain['root']]})
    except (OSError,ValueError):pass
    return {'processes':result,'limited':limited}

def eject(device):
    current=mounts();selected=next((m for m in current if m['name']==device),None)
    if not selected:raise ValueError('USB artık bağlı değil')
    disk=selected['disk'];children=[m for m in current if m['disk']==disk];points=[p for m in children for p in m['mounts']]
    try:
        brain=request('brain','status')
        if brain.get('root') and any(beneath(Path(brain['root']),Path(p)) for p in points):request('brain','lock')
    except (OSError,ValueError):pass
    busy=users_of(points)
    if busy['processes']:raise ValueError('Önce açık dosyaları kapat: '+', '.join(p['name'] for p in busy['processes']))
    # No --force; UDisks performs the authoritative kernel busy check.
    for child in children:
        if child['mounts']:run(['udisksctl','unmount','--block-device',child['name']],30)
    run(['udisksctl','power-off','--block-device',disk],30)
    return 'USB güvenle çıkarılabilir'

class History:
    def __init__(self):self.root=private(STATE/'history')
    def manifest(self):return read(self.root/'index.json',{'roots':{},'files':{}})
    def scan(self,folders=None,retention=None):
        selected=folders if folders is not None else config()['history'];keep=max(2,min(100,retention or config()['retention']));index=self.manifest();added=0;garbage=[];budget=sum(v['size'] for e in index['files'].values() for v in e['versions'])
        for raw in selected:
            root=Path(raw).expanduser().resolve()
            # A whole-home/system snapshot is not an acceptable default.
            if not root.is_dir() or root in (Path('/'),Path.home().resolve()) or beneath(self.root,root):continue
            key=hashlib.sha256(str(root).encode()).hexdigest()[:20];index['roots'][key]=str(root)
            count=0
            for current,dirs,files in os.walk(root,followlinks=False):
                dirs[:]=[d for d in dirs if d not in ('.git','node_modules','__pycache__','backups') and not (Path(current)/d).is_symlink()]
                for name in files:
                    path=Path(current)/name;count+=1
                    if count>10000:break
                    if path.is_symlink() or not path.is_file():continue
                    st=path.stat()
                    if st.st_size>32*1024*1024:continue
                    rel=str(path.relative_to(root));ident=hashlib.sha256((key+'\0'+rel).encode()).hexdigest();entry=index['files'].setdefault(ident,{'root':key,'path':rel,'versions':[]})
                    latest=entry['versions'][-1] if entry['versions'] else {}
                    if latest.get('mtime_ns')==st.st_mtime_ns and latest.get('size')==st.st_size:continue
                    data=path.read_bytes()
                    if path.stat().st_mtime_ns!=st.st_mtime_ns:continue
                    digest=hashlib.sha256(data).hexdigest()
                    if latest.get('sha256')==digest:
                        latest['mtime_ns']=st.st_mtime_ns;continue
                    if budget+len(data)>1024*1024*1024:continue
                    folder=private(self.root/ident);stamp=str(time.time_ns());target=folder/stamp
                    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
                    budget+=len(data)
                    entry['versions'].append({'stamp':stamp,'time':time.time(),'sha256':digest,'size':len(data),'mtime_ns':st.st_mtime_ns});added+=1
                    while len(entry['versions'])>keep:
                        old=entry['versions'].pop(0);budget-=old['size'];garbage.append(folder/old['stamp'])
        atomic(self.root/'index.json',index)
        for old in garbage:old.unlink(missing_ok=True)
        return added
    def restore(self,ident,stamp,destination):
        if not re.fullmatch(r'[0-9a-f]{64}',str(ident)) or not re.fullmatch(r'\d{1,30}',str(stamp)):raise ValueError('Sürüm kimliği geçersiz')
        index=self.manifest();entry=index['files'].get(ident)
        if not entry or not any(v['stamp']==stamp for v in entry['versions']):raise ValueError('Sürüm bulunamadı')
        source=self.root/ident/stamp;data=source.read_bytes();version=next(v for v in entry['versions'] if v['stamp']==stamp)
        if hashlib.sha256(data).hexdigest()!=version['sha256']:raise ValueError('Yedek bütünlüğü bozuk')
        out=Path(destination).expanduser()
        # The GUI chooses an output copy. Never overwrite the live file silently.
        fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f:f.write(data)
        return str(out)

def import_photos(source,destination):
    src=Path(source).resolve();dst=Path(destination).expanduser().resolve()
    if not src.is_dir() or beneath(dst,src):raise ValueError('Kaynak ve hedef klasörleri ayrı olmalı')
    dst.mkdir(parents=True,exist_ok=True);copied=0
    for path in src.rglob('*'):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.jpg','.jpeg','.png','.heic','.dng','.raw','.mp4','.mov'):continue
        if not beneath(path.resolve(),src):continue
        date=dt.datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d');folder=dst/date;folder.mkdir(exist_ok=True)
        target=folder/path.name
        if target.exists():
            if target.stat().st_size==path.stat().st_size and hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256(path.read_bytes()).digest():continue
            target=folder/(path.stem+'-'+hashlib.sha256(path.read_bytes()).hexdigest()[:10]+path.suffix)
        if target.exists():continue
        with path.open('rb') as inp,target.open('xb') as out:shutil.copyfileobj(inp,out)
        shutil.copystat(path,target);copied+=1
    return copied

def network():
    try:
        # UUID avoids punctuation and shell-dependent parsing of SSIDs.
        raw=run(['nmcli','--terse','--fields','UUID,TYPE','connection','show','--active'])
        return next((row.split(':')[0] for row in raw.splitlines() if any(x in row for x in ('wireless','ethernet'))),'')
    except (ValueError,OSError):return ''

def syncthing_status():
    paths=[Path.home()/'.local/state/syncthing/config.xml',Path.home()/'.config/syncthing/config.xml']
    cfg=next((p for p in paths if p.exists()),None)
    if not cfg:return {'available':False,'message':'Syncthing ilk açılışını bekliyor'}
    try:
        xml=ET.parse(cfg).getroot();key=xml.findtext('gui/apikey');address=xml.findtext('gui/address') or '127.0.0.1:8384';secure=xml.find('gui').get('tls')=='true'
        # Never send an API key to a non-loopback address from a changed config.
        if not re.fullmatch(r'(127\.0\.0\.1|localhost):\d+',address):raise ValueError('Panel yalnızca localhost Syncthing arayüzünü okur')
        base=('https' if secure else 'http')+'://'+address
        def get(route):
            req=urllib.request.Request(base+'/rest/'+route,headers={'X-API-Key':key or ''})
            with urllib.request.urlopen(req,timeout=2) as r:return json.load(r)
        connections=get('system/connections');folders=[]
        for node in xml.findall('folder'):
            from urllib.parse import urlencode
            status=get('db/status?'+urlencode({'folder':node.get('id')}));folders.append({'label':node.get('label') or node.get('id'),'state':status.get('state'),'needBytes':status.get('needBytes',0),'needFiles':status.get('needFiles',0),'errors':status.get('errors',0)})
        return {'available':True,'devices':sum(1 for v in connections.get('connections',{}).values() if v.get('connected')),'folders':folders}
    except Exception as e:return {'available':False,'message':str(e)[:250]}

class Processes:
    def __init__(self):self.cache={};self.initial=psutil.net_io_counters(pernic=True)
    def sample(self):
        result=[];new={}
        for process in psutil.process_iter(['pid','name','create_time']):
            try:
                if process.uids().real!=os.getuid():continue
                key=(process.pid,process.create_time());p=self.cache.get(key,process);new[key]=p
                result.append({'pid':p.pid,'born':key[1],'name':p.name(),'cpu':round(p.cpu_percent(),1),'memory':p.memory_info().rss,'status':p.status()})
            except (psutil.Error,OSError):pass
        self.cache=new
        totals={}
        for name,current in psutil.net_io_counters(pernic=True).items():
            start=self.initial.setdefault(name,current);totals[name]={'sent':max(0,current.bytes_sent-start.bytes_sent),'received':max(0,current.bytes_recv-start.bytes_recv)}
        connections=[]
        for p in list(new.values()):
            try:
                for c in p.net_connections(kind='inet'):
                    if c.raddr:connections.append({'pid':p.pid,'name':p.name(),'remote':f'{c.raddr.ip}:{c.raddr.port}','status':c.status})
            except psutil.Error:pass
        return {'apps':sorted({x['name'] for x in result}),'processes':sorted(result,key=lambda x:x['cpu'],reverse=True)[:200],'network':totals,'connections':connections[:500],'sampleTime':time.time()}

def signal_process(pid,born,kill=False):
    p=psutil.Process(int(pid))
    if p.uids().real!=os.getuid() or abs(p.create_time()-float(born))>.001 or p.pid in (os.getpid(),os.getppid()):raise ValueError('İşlem kimliği değişti veya bu işlemi yönetemezsin')
    p.kill() if kill else p.terminate();return 'İşleme sinyal gönderildi'

def diagnostics(destination):
    out=Path(destination)
    if out.exists():raise ValueError('Hedef zaten var')
    entries={'summary.txt':'Violet desktop diagnostics\n'+dt.datetime.now().isoformat()+'\n'}
    for name,args in {'user-services.txt':['systemctl','--user','--failed','--no-pager'],'system-services.txt':['systemctl','--failed','--no-pager'],'desktop-journal.txt':['journalctl','--user','-u','violet-desktop','-u','violet-buds-client','-u','syncthing','-n','150','--no-pager']}.items():
        try:content=run(args)
        except Exception as e:content=str(e)
        content=content.replace(str(Path.home()),'~')
        content=re.sub(r'(?i)((?:token|password|secret|api[-_]?key)\s*[=:]\s*)\S+',r'\1[REDACTED]',content)
        content=re.sub(r'(?i)Bearer\s+\S+','Bearer [REDACTED]',content);entries[name]=content
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED) as z:
        for name,content in entries.items():z.writestr(name,content)
    return str(out)
