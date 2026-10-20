"""Private, versioned desktop state and bounded IPC. No shell evaluation."""
import fcntl,json,os,socket,tempfile
from pathlib import Path
CONFIG=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'violet-desktop'
STATE=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'violet-desktop'
RUNTIME=Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid())))/'violet-desktop'
DEFAULT={'version':1,'snippets':[{'name':'Bugünün tarihi','text':'{date}'},{'name':'Not taslağı','text':'Başlık: {title}\nTarih: {date}\n\nNotlar:\n'}],'history':[],'rules':[],'profiles':[],'presets':[],'palette':[],'retention':25,'commands':[],'searchRoots':[],'phone':'','sessions':[{'id':'example-hukuk','name':'Hukuk','entries':[{'desktop':'org.gnome.Papers.desktop','group':'3','classes':['org.gnome.Papers']},{'desktop':'mybrain-python.desktop','group':'3','classes':['mybrain-python']}]},{'id':'example-kod','name':'Kod','entries':[{'desktop':'kitty.desktop','group':'1','classes':['kitty']},{'desktop':'org.gnome.TextEditor.desktop','group':'1','classes':['org.gnome.TextEditor']}]},{'id':'example-okuma','name':'Okuma','entries':[{'desktop':'org.gnome.Papers.desktop','group':'4','classes':['org.gnome.Papers']},{'desktop':'mybrain-python.desktop','group':'4','classes':['mybrain-python']}]}],'downloadRoot':str(Path.home()/('İndirilenler' if (Path.home()/'İndirilenler').is_dir() and not (Path.home()/'Downloads').is_dir() else 'Downloads')),'downloadAuto':False,'downloadRules':[{'extensions':['pdf'],'folder':'PDF'},{'extensions':['jpg','jpeg','png','webp','gif'],'folder':'Görseller'},{'extensions':['zip','7z','rar','tar','gz','xz'],'folder':'Arşivler'},{'extensions':['appimage','deb','rpm'],'folder':'Kurulum'}],'monitorProfiles':[],'shortcuts':{},'dockPins':None,'panelOrder':['media','dashboard','center','buds','audio','battery','clock'],'motionSpeed':None,'penButton':331,'penSecondary':'eraser'}

def private(path):
    path.mkdir(parents=True,exist_ok=True,mode=0o700)
    if path.is_symlink() or path.stat().st_uid!=os.getuid():raise ValueError('Özel dizinin sahibi/yolu geçersiz')
    os.chmod(path,0o700);return path

def atomic(path,value):
    private(path.parent)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:os.fchmod(f.fileno(),0o600);json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def read(path,default=None):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return default

def config():
    import copy
    value=read(CONFIG/'settings.json',{})
    return {**copy.deepcopy(DEFAULT),**value}

def update(fn):
    private(CONFIG)
    with (CONFIG/'settings.lock').open('a') as lock:
        os.chmod(lock.name,0o600);fcntl.flock(lock,fcntl.LOCK_EX)
        value=config();fn(value);atomic(CONFIG/'settings.json',value);return value

def request(endpoint,action,_timeout=15,**args):
    path=private(RUNTIME)/(endpoint+'.sock')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(_timeout);s.connect(str(path));s.sendall((json.dumps({'action':action,**args})+'\n').encode());raw=b''
        while b'\n' not in raw:
            data=s.recv(65536)
            if not data:raise ValueError('Servis yanıt vermedi')
            raw+=data
            if len(raw)>4*1024*1024:raise ValueError('Yanıt fazla büyük')
    result=json.loads(raw.split(b'\n',1)[0])
    if not result.get('ok'):raise ValueError(result.get('error','İşlem tamamlanamadı'))
    return result.get('data')

def beneath(path,root):
    return path==root or root in path.parents
