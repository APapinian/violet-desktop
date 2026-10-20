"""MRU Alt+Tab with a compositor-owned popup and bounded modifier polling."""
from html import escape

from libqtile import hook, qtile
from libqtile.config import Key
from libqtile.lazy import lazy
from libqtile.log_utils import logger


class Switcher:
    def __init__(self, manager):
        self.q = manager
        self.mru = []
        self.candidates = []
        self.index = 0
        self.active = False
        self.popup = None
        self.timer = None
        self.fallback = None

    def windows(self):
        return {
            wid: window for wid, window in self.q.windows_map.items()
            if getattr(window, "group", None)
            and not hasattr(window.group, "_dropdownconfig")
        }

    def focused(self, window):
        if not window or window.wid not in self.windows() or self.active:
            return
        self.mru = [window.wid] + [wid for wid in self.mru if wid != window.wid]

    def cycle(self, reverse=False, local=False):
        windows = self.windows()
        if local:
            windows = {wid: w for wid, w in windows.items() if w.group == self.q.current_group}
        if not self.active:
            order = [wid for wid in self.mru if wid in windows]
            order += [wid for wid in windows if wid not in order]
            current = getattr(self.q.current_window, "wid", None)
            if current in order:
                order.remove(current)
                order.insert(0, current)
            self.candidates = order
            self.index = 0
        else:
            selected = self.candidates[self.index] if self.candidates else None
            self.candidates = [wid for wid in self.candidates if wid in windows]
            self.index = self.candidates.index(selected) if selected in self.candidates else 0
        if len(self.candidates) < 2:
            self.finish()
            return
        self.active = True
        self.index = (self.index + (-1 if reverse else 1)) % len(self.candidates)
        window = windows[self.candidates[self.index]]
        window.minimized = False
        if window.group.screen and window.group.screen != self.q.current_screen:
            self.q.focus_screen(window.group.screen.index, warp=False)
        elif window.group != self.q.current_group:
            window.group.toscreen()
        window.group.focus(window, warp=False)
        if window.floating:
            window.bring_to_front()
        self.draw(windows)
        if self.timer:
            self.timer.cancel()
        if self.fallback:
            self.fallback.cancel()
        self.timer = self.q.call_later(.04, self.poll)
        # Also works in the currently running, older compositor before logout.
        self.fallback = self.q.call_later(1.0, self.finish)

    def poll(self):
        self.timer = None
        if not self.active:
            return
        try:
            from libqtile.backend.wayland._ffi import lib
            if hasattr(lib, "qw_violet_keyboard_modifiers"):
                if not int(lib.qw_violet_keyboard_modifiers(self.q.core.qw)) & 8:
                    self.finish()
                    return
                if self.fallback:
                    self.fallback.cancel()
                    self.fallback = None
                self.timer = self.q.call_later(.04, self.poll)
        except (ImportError, AttributeError):
            pass

    def emit(self, value):
        import json,os
        from pathlib import Path
        runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))
        if not runtime.is_dir() or runtime.stat().st_uid!=os.getuid():return
        path=runtime/'fatih-switcher.json';temp=runtime/'.fatih-switcher.tmp'
        temp.write_text(json.dumps(value,ensure_ascii=False));temp.chmod(0o600);temp.replace(path)

    def draw(self, windows):
        screen=self.q.current_screen
        self.emit({'active':True,'x':screen.x,'y':screen.y,'rows':[
            {'id':wid,'title':str(windows[wid].name or 'Adsız pencere')[:160],
             'group':windows[wid].group.label or windows[wid].group.name,
             'selected':wid==self.candidates[self.index]}
            for wid in self.candidates]})

    def finish(self):
        self.emit({"active":False,"rows":[]})
        self.active = False
        for timer in (self.timer, self.fallback):
            if timer:
                timer.cancel()
        self.timer = self.fallback = None
        if self.popup:
            self.popup.kill()
            self.popup = None
        self.candidates = []
        self.focused(self.q.current_window)


@hook.subscribe.client_focus
def remember(window):
    switcher = getattr(qtile, "_violet_switcher", None)
    if switcher:
        switcher.focused(window)


@hook.subscribe.startup_complete
def initialize():
    old = getattr(qtile, "_violet_switcher", None)
    if old:
        old.finish()
    qtile._violet_switcher = Switcher(qtile)
    qtile._violet_switcher.focused(qtile.current_window)


@hook.subscribe.shutdown
def shutdown():
    switcher = getattr(qtile, "_violet_switcher", None)
    if switcher:
        switcher.finish()


def cycle(manager, reverse=False, local=False):
    switcher = getattr(manager, "_violet_switcher", None)
    if not switcher:
        switcher = manager._violet_switcher = Switcher(manager)
    switcher.cycle(reverse, local)


def install(config):
    keys = config["keys"]
    # Alt+Tab is explicitly owned by this requested feature.
    identities = [(frozenset(["mod1"]), "Tab"), (frozenset(["mod1", "shift"]), "Tab"),
                  (frozenset(["mod1", "shift"]), "ISO_Left_Tab")]
    keys[:] = [key for key in keys if (frozenset(key.modifiers), key.key) not in identities
               and not getattr(key, "_violet_switcher_owned", False)]
    for modifiers, name, reverse in [( ["mod1"], "Tab", False),
                                     (["mod1", "shift"], "Tab", True),
                                     (["mod1", "shift"], "ISO_Left_Tab", True)]:
        binding = Key(modifiers, name, lazy.function(cycle, reverse=reverse),
                      desc="Pencereler arasında geri geç" if reverse else "Son kullanılan pencereye geç")
        binding._violet_switcher_owned = True
        keys.append(binding)
