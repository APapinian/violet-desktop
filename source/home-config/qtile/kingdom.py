"""Additive Qtile hooks, scratchpads, media popups and Yoga mode handling."""
import ctypes
import json
import os
import re
import subprocess
import time
from pathlib import Path
from libqtile import hook, qtile
from libqtile.config import Key, KeyChord, ScratchPad, DropDown
from libqtile.lazy import lazy
from libqtile.log_utils import logger

RUNTIME=Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))
STATE=Path(os.environ.get('XDG_STATE_HOME',Path.home()/'.local/state'))/'fatih-kingdom'
CONFIG=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'fatih-kingdom'
_timer=None
_keyboard=None
_saved_modes={}
_last_mode=False
_last_transform='normal'
_popup=None
_base_labels={}

def read(path,default=None):
    try:return json.loads(Path(path).read_text())
    except (OSError,ValueError):return {} if default is None else default

def command(args):
    subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)

def panel(name):
    command(['qs','-c','fatih','ipc','call','desktop','feature',name])

def other_screen(q):
    if not q.current_window or len(q.screens)<2:return
    target=(q.current_screen.index+1)%len(q.screens)
    group=q.screens[target].group
    if group:q.current_window.togroup(group.name,switch_group=False);q.focus_screen(target)

def _config():
    defaults=read(CONFIG/'defaults.json');custom=read(CONFIG/'settings.json')
    for k,v in custom.items():
        if isinstance(v,dict) and isinstance(defaults.get(k),dict):defaults[k].update(v)
        else:defaults[k]=v
    return defaults

def is_game(window,c):
    names=window.get_wm_class() or [] if window else []
    for pattern in c.get('games',{}).get('classes',[]):
        try:
            if any(re.fullmatch(pattern,n,re.I) for n in names):return True
        except re.error:pass
    return False

def publish():
    if not qtile.current_screen:return
    try:
        c=_config();window=qtile.current_window
        base=read(RUNTIME/'fatih-qtile.json')
        # Retain the welcome-session and other bridge fields; refresh live geometry.
        names=window.get_wm_class() or [] if window else []
        base.update(session=os.getpid(),active=qtile.current_group.name if qtile.current_group else '1',
                    title=window.name if window else 'Masaüstü',application=names[-1] if names else None,
                    game=is_game(window,c),geometry={k:getattr(window,k) for k in ('x','y','width','height')} if window else None,
                    groups=[dict(name=g.name,label=g.label or g.name,occupied=bool(g.windows)) for g in qtile.groups if g.name!='kingdom-scratch'])
        # VIOLET_WORKSPACES_V5
        from violet_workspaces import snapshot as _violet_snapshot
        base.update(_violet_snapshot(qtile))
        path=RUNTIME/'fatih-qtile.json';tmp=path.with_suffix('.kingdom.tmp');tmp.write_text(json.dumps(base,ensure_ascii=False));tmp.chmod(0o600);tmp.replace(path)
        path=RUNTIME/'fatih-kingdom-qtile.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(base,ensure_ascii=False));tmp.chmod(0o600);tmp.replace(path)
    except Exception:logger.exception('Kingdom bridge')

def _internal_devices(disable):
    """Override only the built-in keyboard/touchpad; restore their prior modes."""
    from libqtile.backend.wayland._ffi import ffi,lib
    api=ctypes.CDLL('libinput.so.10')
    api.libinput_device_config_send_events_get_mode.argtypes=[ctypes.c_void_p]
    api.libinput_device_config_send_events_get_mode.restype=ctypes.c_uint32
    api.libinput_device_config_send_events_set_mode.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    api.libinput_device_config_send_events_set_mode.restype=ctypes.c_int
    found=set()
    @ffi.callback('void(struct qw_input_device *, char *, int, int, int)')
    def each(device,name,typ,vendor,product):
        text=ffi.string(name).decode()
        if text not in ('AT Translated Set 2 keyboard','GXTP5100:00 27C6:01E0 Touchpad'):return
        raw=lib.qw_input_device_get_libinput_handle(device)
        if raw==ffi.NULL:return
        ptr=int(ffi.cast('uintptr_t',raw));found.add((text,ptr));key=(text,ptr)
        if disable:
            if key not in _saved_modes:_saved_modes[key]=api.libinput_device_config_send_events_get_mode(ptr)
            if api.libinput_device_config_send_events_set_mode(ptr,1)!=0:logger.warning('Tablet input mode unavailable: %s',text)
        elif key in _saved_modes:
            api.libinput_device_config_send_events_set_mode(ptr,_saved_modes.pop(key))
    lib.qw_server_loop_input_devices(qtile.core.qw,each)
    for key in set(_saved_modes)-found:_saved_modes.pop(key,None)

def tick():
    global _timer,_keyboard,_last_mode,_last_transform
    try:
        state=read(RUNTIME/'fatih-kingdom/state.json');t=state.get('tablet',{});s=t.get('settings',{})
        override=t.get('override');mode=(bool(t.get('tablet')) if s.get('automatic',True) else False) if override is None else bool(override)
        if mode!=_last_mode:
            _internal_devices(mode);_last_mode=mode
        if mode and s.get('keyboard') and (_keyboard is None or _keyboard.poll() is not None):
            _keyboard=subprocess.Popen(['wvkbd-mobintl'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        elif (not mode or not s.get('keyboard')) and _keyboard and _keyboard.poll() is None:
            _keyboard.terminate();_keyboard=None
        orientation=read(RUNTIME/'fatih-kingdom/orientation.json')
        transform={'normal':'normal','bottom-up':'180','left-up':'90','right-up':'270'}.get(orientation.get('orientation'),'normal') if mode and s.get('rotation') and orientation.get('available') else 'normal'
        if transform!=_last_transform:
            # Never wait for a Wayland client inside the compositor event loop.
            command(['wlr-randr','--output',s.get('output','eDP-1'),'--transform',transform])
            _last_transform=transform
        for group in qtile.groups:
            if group.name=='kingdom-scratch':continue
            if group.name not in _base_labels:_base_labels[group.name]=group.label or group.name
            icons=[]
            for win in group.windows:
                names=' '.join(win.get_wm_class() or []).lower()
                icon='󰈹' if 'firefox' in names else '' if any(x in names for x in ('foot','konsole')) else '󰎆' if 'mpv' in names else '󰨞' if 'code' in names else '◇'
                if icon not in icons:icons.append(icon)
            label=_base_labels[group.name]+('  '+''.join(icons[:3]) if icons else '')
            if label!=group.label:group.set_label(label)
        publish()
    except Exception:logger.exception('Kingdom mode update')
    _timer=qtile.call_later(2,tick)

def rules(window):
    c=_config();names=window.get_wm_class() or []
    if window.group and window.group.name=='kingdom-scratch':return
    defaults=[dict(pattern='(?i)(chromium|google-chrome)',group='2'),dict(pattern='(?i)(code|codium|jetbrains.*)',group='1'),dict(pattern='(?i)(mpv|vlc)',group='5'),dict(pattern='(?i)(pavucontrol|blueman-manager|kingdom-overlay)',floating=True)]
    for rule in defaults+c.get('applicationRules',[]):
        try:
            if not any(re.fullmatch(rule['pattern'],n) for n in names):continue
            if rule.get('group') in qtile.groups_map and not any('firefox' in n.lower() for n in names) and not (window.group and window.group.name=='kingdom-scratch'):window.togroup(rule['group'])
            if rule.get('floating'):window.enable_floating()
        except Exception:logger.warning('Invalid kingdom window rule')
    publish()

def extras_popup(queue=False):
    global _popup
    try:
        from qtile_extras.popup.toolkit import PopupRelativeLayout,PopupText,PopupImage
        state=read(RUNTIME/'fatih-kingdom/state.json');current=(state.get('providers',{}).get('media',{}).get('data') or {}).get('current') or {}
        controls=[PopupText(text='Sıradaki melodiler' if queue else current.get('title','Henüz bir şey çalmıyor'),pos_x=.06,pos_y=.06,width=.88,height=.18,fontsize=18,foreground='c5b4ff')]
        cover=current.get('cover')
        if cover and Path(cover).is_file():controls.append(PopupImage(filename=cover,pos_x=.06,pos_y=.29,width=.3,height=.6))
        items=state.get('upcoming',[])
        text='\n'.join(e.get('title','') for e in items[:3]) if queue else current.get('artist','')+'\n'+current.get('album','')
        controls.append(PopupText(text=text or 'Bu oynatıcı sıra paylaşmıyor',pos_x=.4,pos_y=.3,width=.54,height=.58,wrap=True,fontsize=13,foreground='ece4f8'))
        if _popup:_popup.kill()
        _popup=PopupRelativeLayout(qtile,width=510,height=250,controls=controls,background='17151f',hide_on_timeout=7)
        _popup.show(centered=True)
    except Exception:logger.exception('qtile-extras media popup');panel('media')

def start():
    global _timer
    command(['systemctl','--user','start','fatih-kingdom.service','fatih-clipboard.service'])
    c=_config()
    for name,layout in c.get('groupLayouts',{'1':'monadtall','2':'max','5':'max'}).items():
        group=qtile.groups_map.get(name)
        if group:
            try:group.setlayout(layout)
            except Exception:pass
    if _timer:_timer.cancel()
    _timer=qtile.call_later(2,tick)

def stop():
    global _timer,_keyboard
    if _timer:_timer.cancel();_timer=None
    if _keyboard and _keyboard.poll() is None:_keyboard.terminate()
    try:_internal_devices(False)
    except Exception:pass
    if _last_transform!='normal':command(['wlr-randr','--output','eDP-1','--transform','normal'])
    command(['systemctl','--user','stop','fatih-kingdom.service','fatih-clipboard.service'])

def install(config):
    """Called once at the end of config.py. No palette/layout replacement."""
    mod=config.get('mod','mod4');keys=config['keys'];groups=config['groups']
    if not any(g.name=='kingdom-scratch' for g in groups):
        groups.append(ScratchPad('kingdom-scratch',[
            DropDown('terminal','foot --app-id=kingdom-terminal',x=.08,y=.09,width=.84,height=.65,opacity=.98,on_focus_lost_hide=True),
        ],single=True))
    sub=[]
    for key,name in [('d','daily'),('m','media'),('y','music'),('v','video'),('r','reddit'),('f','feeds'),('s','system'),('p','pomodoro'),('n','notes'),('c','calculator'),('e','emoji'),('b','clipboard'),('w','weather'),('a','accounts'),('g','finance'),('t','tablet'),('k','power'),('i','settings'),('o','connectivity'),('h','commands')]:
        sub.append(Key([],key,lazy.function(lambda q,n=name:panel(n)),desc='Krallık: '+name))
    sub.extend([Key([],'Return',lazy.group['kingdom-scratch'].dropdown_toggle('terminal')),Key([],'l',lazy.function(lambda q:command(['kingdomctl','translation']))),
                Key([],'x',lazy.function(other_screen)),Key([],'u',lazy.function(lambda q:extras_popup())),Key([],'q',lazy.function(lambda q:extras_popup(True))),
                Key([],'z',lazy.function(lambda q:command(['kingdom-overlay'])))])
    if not any(k.key=='F12' and set(k.modifiers)=={mod} for k in keys):keys.append(KeyChord([mod],'F12',sub,name='Krallık'))
    hook.subscribe.startup(start);hook.subscribe.startup_complete(start);hook.subscribe.shutdown(stop)
    hook.subscribe.client_managed(rules)
    for event in ('client_focus','client_killed','setgroup','group_window_add','layout_change','current_screen_change','client_name_updated','float_change','screens_reconfigured'):
        getattr(hook.subscribe,event)(lambda *args:publish())
