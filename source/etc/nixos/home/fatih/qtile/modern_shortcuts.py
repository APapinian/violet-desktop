"""Modern desktop entry points, merged before the existing shortcut registry."""
from libqtile import hook
from libqtile.config import Key
from libqtile.lazy import lazy
import subprocess

def panel(tab):
    subprocess.Popen(['qs','-c','fatih','ipc','call','desktop','modern',tab],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def install(config):
    from desktop_suite import install as install_suite
    install_suite(config)
    keys=config['keys'];mod=config.get('mod','mod4')
    keys[:]=[k for k in keys if not getattr(k,'_violet_modern_owned',False)]
    occupied={(tuple(sorted(k.modifiers)),k.key.lower()) for k in keys}
    def add(mods,key,action,label):
        if (tuple(sorted(mods)),key.lower()) in occupied:return
        binding=Key(mods,key,action,desc=label);binding._violet_modern_owned=True;keys.append(binding)
    add([mod,'mod1'],'m',lazy.function(lambda q:panel('media')),'Violet plaklı oynatıcı')
    add([mod,'mod1'],'b',lazy.function(lambda q:panel('buds')),'Galaxy Buds / pil paneli')
    add([mod,'mod1'],'d',lazy.function(lambda q:panel('dashboard')),'Violet günlük panel')
    add([mod,'mod1'],'n',lazy.spawn('mybrain-python'),'MyBrain · Python')
    add([mod,'mod1'],'e',lazy.spawn('nautilus'),'Dosyalar · Nautilus')
    add([mod,'mod1'],'o',lazy.spawn('kingdom-overlay'),'Şimdi çalıyor kartı')

