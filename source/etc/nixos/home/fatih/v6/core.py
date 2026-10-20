"""Bounded OpenAI and Telegram clients; no shell evaluation or secret logging."""
import json, os, re, subprocess, time, urllib.request, urllib.error
from pathlib import Path

CONFIG=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'violet-agent'
ACTIONS=['none','status','firefox','files','terminal','mybrain','play-pause','next','previous','volume','brightness','lock']

def load(name):
    path=CONFIG/name
    if not path.exists():return {}
    if path.is_symlink() or path.stat().st_uid!=os.getuid() or path.stat().st_mode & 0o077:
        raise ValueError('Kimlik dosyası kullanıcıya özel olmalı: chmod 600 '+str(path))
    return json.loads(path.read_text())

def save(name,value):
    CONFIG.mkdir(mode=0o700,parents=True,exist_ok=True)
    if CONFIG.is_symlink():raise ValueError('Ayar dizini bir bağ olamaz')
    os.chmod(CONFIG,0o700)
    target=CONFIG/name;tmp=CONFIG/(name+'.tmp')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2)
        os.replace(tmp,target)
    finally:tmp.unlink(missing_ok=True)

def run(argv):
    result=subprocess.run(argv,capture_output=True,text=True,timeout=15)
    if result.returncode:raise ValueError((result.stderr.strip() or 'Komut başarısız')[:600])
    return result.stdout.strip()[:3000]

def status():
    import platform,shutil
    disk=shutil.disk_usage(Path.home())
    return f'{platform.node()} · {platform.release()}\nDisk boş: {disk.free/2**30:.1f} GiB\n'+run(['uptime'])

def validate(action,value=0):
    if action not in ACTIONS:raise ValueError('Desteklenmeyen işlem')
    if isinstance(value,bool) or not isinstance(value,int):raise ValueError('İşlem değeri tam sayı olmalı')
    if action in ('volume','brightness') and not 0<=value<=100:raise ValueError('Yüzde 0–100 arasında olmalı')
    return action,value

def execute(action,value=0):
    validate(action,value)
    if action=='none':return 'Bir işlem önerilmedi.'
    if action=='status':return status()
    commands={
        'firefox':['firefox'],'files':['nautilus'],'terminal':['kitty'],'mybrain':['mybrain-python'],
        'play-pause':['playerctl','play-pause'],'next':['playerctl','next'],'previous':['playerctl','previous'],
        'volume':['wpctl','set-volume','-l','1.0','@DEFAULT_AUDIO_SINK@',f'{value}%'],
        'brightness':['brightnessctl','set',f'{max(1,value)}%'],'lock':['loginctl','lock-session']}
    if action in ('firefox','files','terminal','mybrain'):
        subprocess.Popen(commands[action],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        return 'Uygulama açıldı.'
    return run(commands[action]) or 'İşlem uygulandı.'

def post(url,payload,headers=None,timeout=45):
    req=urllib.request.Request(url,json.dumps(payload).encode(),{'Content-Type':'application/json',**(headers or {})})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:raise ValueError('Yanıt sınırı aşıldı')
            return json.loads(raw)
    except urllib.error.HTTPError as e:raise ValueError(f'Servis HTTP {e.code}; anahtar, model erişimi ve bakiyeyi kontrol et.') from None
    except urllib.error.URLError:raise ValueError('Servise bağlanılamadı.') from None

def ask(messages,settings):
    key=settings.get('api_key','').strip();model=settings.get('model','gpt-5.6-luna').strip()
    if not key:raise ValueError('Ayarlar bölümünden OpenAI API anahtarını gir.')
    if not re.fullmatch(r'[a-zA-Z0-9._:-]{1,100}',model):raise ValueError('Model kimliği geçersiz')
    schema={'type':'object','properties':{'answer':{'type':'string'},'action':{'type':'string','enum':ACTIONS},'value':{'type':'integer'}},'required':['answer','action','value'],'additionalProperties':False}
    result=post('https://api.openai.com/v1/responses',{
        'model':model,'store':False,'max_output_tokens':800,'reasoning':{'effort':'none'},
        'instructions':'Violet/Hyrule masaüstü yardımcısısın. Türkçe, kısa cevap ver. İşlem istenirse yalnız verilen enum içinden bir öneri seç. Komut çalıştırdığını iddia etme; kullanıcı GUI düğmesiyle uygulayacak. Genel sorularda none seç. volume ve brightness için value 0-100; diğerleri 0. Gizli dosya veya komut isteyemezsin.',
        'input':messages[-8:],'text':{'format':{'type':'json_schema','name':'desktop_proposal','strict':True,'schema':schema}}
    },{'Authorization':'Bearer '+key})
    output=''.join(c.get('text','') for item in result.get('output',[]) if item.get('type')=='message' for c in item.get('content',[]) if c.get('type')=='output_text')
    if not output:raise ValueError('Model metin üretmedi; çıktı sınırını veya model desteğini kontrol et.')
    value=json.loads(output);validate(value['action'],value['value']);value['usage']=result.get('usage',{})
    return value

def telegram(method,payload,token):
    if not re.fullmatch(r'\d+:[A-Za-z0-9_-]+',token):raise ValueError('Bot token biçimi geçersiz')
    value=post('https://api.telegram.org/bot'+token+'/'+method,payload,timeout=40)
    if not value.get('ok'):raise ValueError('Telegram isteği başarısız')
    return value['result']

def remote_command(text):
    parts=text.strip().split();cmd=parts[0].split('@')[0] if parts else ''
    mapping={'/status':'status','/play':'play-pause','/next':'next','/previous':'previous','/lock':'lock'}
    if cmd=='/help':return '/status /play /next /previous /volume 0-100 /brightness 0-100 /lock'
    if cmd in mapping and len(parts)==1:return execute(mapping[cmd])
    if cmd in ('/volume','/brightness') and len(parts)==2:
        try:value=int(parts[1])
        except ValueError:raise ValueError('Yüzde tam sayı olmalı') from None
        return execute(cmd[1:],value)
    return 'Komut bulunamadı. /help'

def bot_loop():
    settings=load('remote.json');token=settings.get('token','')
    users=set(settings.get('users',[]));chats=set(settings.get('chats',[]))
    if not users or not chats or not all(isinstance(v,int) for v in users|chats):
        raise ValueError('İzinli kullanıcı ve sohbet kimliklerini ayarlamalısın.')
    telegram('getMe',{},token)
    # Drop accumulated updates on startup; never replay old remote commands.
    pending=telegram('getUpdates',{'offset':-1,'timeout':0,'allowed_updates':['message']},token)
    offset=max([r['update_id']+1 for r in pending],default=0)
    while True:
        try:
            updates=telegram('getUpdates',{'offset':offset,'timeout':25,'allowed_updates':['message']},token)
            for update in updates:
                offset=update['update_id']+1;m=update.get('message',{})
                if m.get('from',{}).get('id') not in users or m.get('chat',{}).get('id') not in chats:continue
                if time.time()-m.get('date',0)>60:continue
                try:reply=remote_command(m.get('text','')[:300])
                except Exception as e:reply='İşlem uygulanamadı: '+str(e)[:500]
                telegram('sendMessage',{'chat_id':m['chat']['id'],'text':reply[:3500]},token)
        except Exception:
            # Deliberately exclude token-bearing request URLs from logs.
            time.sleep(5)
