"""Additional shortcuts with an inventory of the bindings that actually loaded."""
import json
import os
import subprocess
from pathlib import Path
from libqtile.config import Key, KeyChord
from libqtile.lazy import lazy
from libqtile.log_utils import logger

ALIASES={'super':'mod4','ctrl':'control','alt':'mod1'}
LABELS={'mod4':'Super','mod1':'Alt','control':'Ctrl','shift':'Shift'}
DIRECT=[
    ('d','daily','Günlük panel'),('m','media','Müzik / MPRIS'),
    ('y','music','YouTube Music'),('v','video','Video arama'),
    ('n','notes','Hızlı notlar'),('p','pomodoro','Pomodoro'),
    ('w','weather','Hava ve namaz vakitleri'),('b','clipboard','Pano geçmişi'),
    ('t','tablet','Tablet modu ayarları'),('s','system','Sistem durumu'),
    ('g','finance','Döviz / altın / kripto'),('a','accounts','Hesaplar ve bildirimler'),
    ('e','emoji','Emoji seçici'),('o','connectivity','Wi-Fi / Bluetooth'),
    ('i','settings','Krallık ayarları'),('h','commands','Kayıtlı komutlar'),
    ('k','power','Güç menüsü'),('c','calculator','Hesap makinesi'),
    ('f','feeds','RSS / YouTube / Reddit / podcast'),
]

def canonical(modifiers,key):
    return tuple(sorted({ALIASES.get(m.lower(),m.lower()) for m in modifiers})),str(key).lower()

def combo(modifiers,key):
    names=[LABELS.get(m,m) for m in ('mod4','control','mod1','shift') if m in canonical(modifiers,key)[0]]
    names += [m for m in canonical(modifiers,key)[0] if m not in LABELS]
    return '+'.join(names+[{'Return':'Enter','space':'Space','Left':'←','Right':'→','Up':'↑','Down':'↓','Print':'Print Screen'}.get(key,str(key))])

def spawn(args):
    subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)

def desktop(method):
    spawn(['qs','-c','fatih','ipc','call','desktop',method])

def feature(name):
    spawn(['qs','-c','fatih','ipc','call','desktop','feature',name])

def registry(keys,prefix=''):
    rows=[]
    for key in keys:
        title=prefix+combo(key.modifiers,key.key)
        if isinstance(key,KeyChord):
            rows.append(dict(combo=title,label=key.desc or key.name or 'Tuş dizisi',category='Tuş dizileri',status='active'))
            rows+=registry(key.submappings,title+' → ')
        else:
            desc=key.desc
            if not desc:
                calls=[]
                for command in getattr(key,'commands',[]):
                    name=getattr(command,'name','')
                    selectors=getattr(command,'selectors',[])
                    path='.'.join(str(part[0]) for part in selectors)
                    args=getattr(command,'args',())
                    if name=='spawn' and args: calls.append(str(args[0]))
                    elif name: calls.append((path+'.' if path else '')+name)
                desc=' · '.join(calls) or 'Mevcut tuş ataması'
            rows.append(dict(combo=title,label=desc,category='Mevcut kısayollar',status='active'))
    return rows

def install(config,has_features=True):
    mod=config.get('mod','mod4');keys=config['keys']
    # Some modular configurations reuse their keys.py list during a reload.
    # Recreate only bindings owned by this add-on; retain every user's binding.
    keys[:]=[key for key in keys if not getattr(key,'_hyrule_violet_owned',False)]
    occupied={canonical(k.modifiers,k.key) for k in keys}
    extras=[];skipped=[]
    def add(modifiers,key,call,label,category='Krallık panelleri'):
        identity=canonical(modifiers,key)
        row=dict(combo=combo(modifiers,key),label=label,category=category,status='active')
        if identity in occupied:
            row['status']='conflict';skipped.append(row)
            logger.info('Violet shortcut retained existing binding: %s',row['combo']);return
        occupied.add(identity);binding=Key(modifiers,key,call,desc=label)
        binding._hyrule_violet_owned=True;keys.append(binding);extras.append(row)
    add([mod],'F1',lazy.function(lambda q:desktop('shortcuts')),'Kısayol rehberi','Masaüstü')
    add([mod,'control'],'F1',lazy.function(lambda q:desktop('settings')),'Qtile masaüstü ayarları','Masaüstü')
    add([mod,'control'],'F2',lazy.function(lambda q:desktop('toggle')),'Kontrol merkezi','Masaüstü')
    for key,name,label in [('F3','audio','Ses ayarları'),('F4','clock','Saat / takvim'),('F5','battery','Pil / güç profili')]:
        add([mod,'control'],key,lazy.function(lambda q,n=name:desktop(n)),label,'Masaüstü')
    add([mod,'control'],'F6',lazy.function(lambda q:desktop('welcome')),'Karşılama animasyonunu göster','Masaüstü')
    add([mod,'control'],'F7',lazy.spawn('playerctl previous'),'Önceki şarkı','Medya')
    add([mod,'control'],'F8',lazy.spawn('playerctl play-pause'),'Oynat / duraklat','Medya')
    add([mod,'control'],'F9',lazy.spawn('playerctl next'),'Sonraki şarkı','Medya')
    add([mod],'Escape',lazy.function(lambda q:desktop('close')),'Açık paneli kapat','Masaüstü')
    if has_features:
        for key,name,label in DIRECT:
            add([mod,'control'],key,lazy.function(lambda q,n=name:feature(n)),label)
        add([mod,'mod1'],'r',lazy.function(lambda q:feature('reddit')),'Reddit','Krallık panelleri')
        add([mod,'control'],'l',lazy.spawn('kingdomctl translation'),'LinguaMap çeviri','Araçlar')
        add([mod,'control'],'Return',lazy.group['kingdom-scratch'].dropdown_toggle('terminal'),'Quake terminal','Araçlar')
        from kingdom import other_screen,extras_popup
        add([mod,'control'],'Right',lazy.function(other_screen),'Pencereyi diğer ekrana gönder','Pencereler')
        add([mod,'control'],'u',lazy.function(lambda q:extras_popup()),'Albüm kapağı kartı','Medya')
        add([mod,'control'],'j',lazy.function(lambda q:extras_popup(True)),'Sıradaki üç şarkı','Medya')
        for modifiers,kind,label in [([], 'screen','Tüm ekranı kaydet'),(['shift'],'area','Alanı seç ve kaydet'),(['control'],'window','Aktif pencereyi kaydet')]:
            add(modifiers,'Print',lazy.function(lambda q,k=kind:spawn(['kingdomctl','screenshot',json.dumps(k)])),label,'Ekran görüntüsü')
    else:
        logger.info('Violet: Kingdom features are not installed; only existing shell actions added.')
    rows=registry(keys)
    lookup={row['combo']:row for row in extras}
    rows=[lookup.get(row['combo'],row) for row in rows]+skipped
    payload={'version':1,'rows':rows,'has_features':has_features,'conflicts':len(skipped)}
    try:
        runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))
        if not runtime.is_dir() or runtime.stat().st_uid!=os.getuid():raise OSError('Owned runtime directory missing')
        path=runtime/'fatih-shortcuts.json';temp=runtime/f'.fatih-shortcuts-{os.getpid()}.tmp'
        with temp.open('x',encoding='utf-8') as f:
            os.chmod(temp,0o600);json.dump(payload,f,ensure_ascii=False);f.write('\n')
        temp.replace(path)
    except OSError:logger.exception('Violet shortcut inventory could not be written')
