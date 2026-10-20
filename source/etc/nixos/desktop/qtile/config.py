import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from libqtile import hook, qtile
from libqtile.config import Click, Drag, Match, Screen
from libqtile.lazy import lazy
from libqtile.backend.wayland import InputConfig
from keys import keys
from groups import groups
from layouts import layouts, floating_layout
from bridge import publish

# Quickshell owns the panel and reserves its space via layer-shell.
screens = [Screen()]
mouse = [
    Drag(['mod4'], 'Button1', lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag(['mod4'], 'Button3', lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click(['mod4'], 'Button2', lazy.window.bring_to_front()),
]
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = 'smart'
reconfigure_screens = True
wl_input_rules = {
    'type:keyboard': InputConfig(kb_layout='tr'),
    '10182:480:GXTP5100:00 27C6:01E0 Touchpad': InputConfig(
        tap=True, natural_scroll=False, pointer_accel=0.2, scroll_method='two_finger'),
}
wmname = 'Qtile'

@hook.subscribe.startup_once
def start_desktop():
    qtile.spawn('fatih-desktop-start')

@hook.subscribe.startup_complete
@hook.subscribe.setgroup
@hook.subscribe.client_focus
@hook.subscribe.client_name_updated
@hook.subscribe.client_managed
@hook.subscribe.client_killed
@hook.subscribe.current_screen_change
def update_shell(*args):
    publish()

@hook.subscribe.shutdown
def stop_desktop():
    qtile.spawn('qs -c fatih ipc call desktop quit')
