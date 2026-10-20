from libqtile.config import Key
from libqtile.lazy import lazy
from groups import groups
mod = 'mod4'
keys = [
    Key([mod], 'Return', lazy.spawn('foot')),
    Key([mod], 'd', lazy.spawn('rofi -show drun')),
    Key([mod], 'a', lazy.spawn('qs -c fatih ipc call desktop toggle')),
    Key([mod], 'q', lazy.window.kill()),
    Key([mod, 'control'], 'r', lazy.reload_config()),
    Key([mod, 'control'], 'q', lazy.shutdown()),
    Key([mod], 'space', lazy.next_layout()),
    Key([mod], 'f', lazy.window.toggle_fullscreen()),
    Key([mod, 'shift'], 'space', lazy.window.toggle_floating()),
    Key([], 'XF86AudioRaiseVolume', lazy.spawn('wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+')),
    Key([], 'XF86AudioLowerVolume', lazy.spawn('wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-')),
    Key([], 'XF86AudioMute', lazy.spawn('wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle')),
    Key([], 'XF86MonBrightnessUp', lazy.spawn('brightnessctl set +5%')),
    Key([], 'XF86MonBrightnessDown', lazy.spawn('brightnessctl set 5%-')),
]
for key, action in [('h', 'left'), ('j', 'down'), ('k', 'up'), ('l', 'right')]:
    keys.append(Key([mod], key, getattr(lazy.layout, action)()))
    keys.append(Key([mod, 'shift'], key, getattr(lazy.layout, 'shuffle_' + action)()))
for group in groups:
    keys.extend([
        Key([mod], group.name, lazy.group[group.name].toscreen()),
        Key([mod, 'shift'], group.name, lazy.window.togroup(group.name)),
    ])
