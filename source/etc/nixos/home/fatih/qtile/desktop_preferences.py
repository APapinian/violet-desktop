"""Optional user preferences: keep system input rules until valid preferences exist."""
import json
import math
import os
from pathlib import Path
from libqtile.backend.wayland import InputConfig

TOUCHPAD = '10182:480:GXTP5100:00 27C6:01E0 Touchpad'

def read_preferences():
    state = Path(os.environ.get('XDG_STATE_HOME') or (Path.home() / '.local/state'))
    try:
        data = json.loads((state / 'fatih-desktop/preferences.json').read_text())
        return data if isinstance(data, dict) and data.get('version') == 1 else {}
    except (OSError, ValueError):
        return {}

def copy_rule(rule):
    if rule is None:
        return {}
    return {name: getattr(rule, name, default) for name, default, _ in InputConfig.defaults}

def apply_preferences(rules, current_focus, current_cursor_size=24):
    data = read_preferences()
    if not data or not isinstance(rules, dict):
        return current_focus, current_cursor_size
    accel = data.get('pointerAccel')
    shared = {}
    if isinstance(accel, (float, int)) and not isinstance(accel, bool) and math.isfinite(accel):
        shared['pointer_accel'] = max(-1.0, min(1.0, accel))
    if data.get('pointerProfile') in ('adaptive', 'flat'):
        shared['accel_profile'] = data['pointerProfile']
    if shared:
        mouse = copy_rule(rules.get('type:pointer'))
        mouse.update(shared)
        rules['type:pointer'] = InputConfig(**mouse)
    # Keep the existing exact rule and all of its other settings.
    if TOUCHPAD in rules:
        touchpad = copy_rule(rules[TOUCHPAD])
        touchpad.update(shared)
        for key, option in [('naturalScroll', 'natural_scroll'), ('tapToClick', 'tap'), ('disableWhileTyping', 'dwt')]:
            if type(data.get(key)) is bool:
                touchpad[option] = data[key]
        rules[TOUCHPAD] = InputConfig(**touchpad)
    focus = data.get('focusFollowsMouse', current_focus)
    if type(focus) is not bool:
        focus = current_focus
    size = data.get('cursorSize', current_cursor_size)
    if type(size) is not int or size not in (24, 32, 40):
        size = current_cursor_size
    return focus, size
