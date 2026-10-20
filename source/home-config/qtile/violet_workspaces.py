"""Screen-aware numbered workspaces and the shell's exact window inventory."""
import json
import os
from pathlib import Path


def select_group(q, name):
    group = q.groups_map.get(str(name))
    if group is None or not q.current_screen:
        return
    if group.screen is not None:
        q.focus_screen(group.screen.index)
    else:
        group.toscreen(q.current_screen.index, toggle=False)


def move_window(q, name, follow=False):
    window = q.current_window
    if window is None or str(name) not in q.groups_map:
        return
    window.togroup(str(name), switch_group=False)
    if follow:
        select_group(q, str(name))


def snapshot(q):
    screens = []
    windows = []
    for screen in q.screens:
        group = screen.group
        focused = group.current_window if group else None
        screens.append(dict(index=screen.index, x=screen.x, y=screen.y,
                            width=screen.width, height=screen.height,
                            group=group.name if group else "",
                            focused=screen is q.current_screen,
                            title=(focused.name or "Masaüstü") if focused else "Masaüstü",
                            fullscreen=bool(focused and focused.fullscreen)))
    for group in q.groups:
        if group.name == "kingdom-scratch":
            continue
        for window in sorted(group.windows, key=lambda w: w.wid):
            names = window.get_wm_class() or []
            windows.append(dict(id=window.wid, group=group.name,
                                title=window.name or "Pencere", appId=names[-1] if names else "",
                                classes=list(names), activated=window is group.current_window,
                                fullscreen=bool(window.fullscreen)))
    return dict(violetWorkspaces=5, screens=screens, windows=windows)


def install(config):
    from libqtile.config import Key
    from libqtile.lazy import lazy
    mod = config.get("mod", "mod4")
    keys = config["keys"]
    numbers = {str(n) for n in range(1, 10)}
    replace = ({mod}, {mod, "shift"})
    keys[:] = [k for k in keys if not (str(k.key) in numbers and set(k.modifiers) in replace)]
    for name in sorted(numbers):
        keys.append(Key([mod], name, lazy.function(select_group, name),
                        desc=f"Masaüstü {name}: bulunduğu ekrana odaklan / burada aç"))
        keys.append(Key([mod, "shift"], name, lazy.function(move_window, name),
                        desc=f"Pencereyi masaüstü {name} üzerine taşı"))
        modifiers = [mod, "control", "shift"]
        if not any(str(k.key) == name and set(k.modifiers) == set(modifiers) for k in keys):
            keys.append(Key(modifiers, name, lazy.function(move_window, name, True),
                            desc=f"Pencereyi masaüstü {name} üzerine taşı ve takip et"))
    # Refresh the existing shortcut guide after replacing the numbered bindings.
    try:
        from violet_shortcuts import registry
        path = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "fatih-shortcuts.json"
        payload = json.loads(path.read_text())
        conflicts = [row for row in payload.get("rows", []) if row.get("status") == "conflict"]
        payload["rows"] = registry(keys) + conflicts
        temp = path.with_suffix(".violet.tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False)); temp.chmod(0o600); temp.replace(path)
    except (OSError, ValueError, ImportError):
        pass
