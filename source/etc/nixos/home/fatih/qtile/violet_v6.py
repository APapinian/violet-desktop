"""Canonical Violet controls and an in-session horizontal viewport layout."""
from libqtile import hook, qtile
from libqtile.config import Key
from libqtile.lazy import lazy
from libqtile.layout.base import _SimpleLayoutBase
from libqtile.command.base import expose_command


class HyruleScroll(_SimpleLayoutBase):
    """A horizontal row: focus scrolls the viewport, other clients are hidden."""
    defaults = [('ratio', .62, 'Column width as fraction of output'),
                ('margin', 12, 'Outer gap'), ('border_width', 2, 'Border'),
                ('border_focus', '#c5b4ff', 'Active'), ('border_normal', '#302c3c', 'Inactive')]

    def __init__(self, **config):
        super().__init__(**config)
        self.add_defaults(HyruleScroll.defaults)
        self.name = 'hyrule-scroll'

    def configure(self, client, screen_rect):
        if not self.clients.clients:
            return
        index = self.clients.clients.index(client)
        focus = self.clients.current_index
        width = max(160, int(screen_rect.width * self.ratio))
        # The focused column stays centered; adjacent columns remain partially visible.
        x = screen_rect.x + (screen_rect.width - width)//2 + (index - focus)*width
        left = max(screen_rect.x, x)
        right = min(screen_rect.x + screen_rect.width, x + width)
        if right-left <= 2*self.margin + 2*self.border_width:
            client.hide()
            return
        client.place(left+self.margin, screen_rect.y+self.margin,
                     right-left-2*self.margin-2*self.border_width,
                     screen_rect.height-2*self.margin-2*self.border_width,
                     self.border_width,
                     self.border_focus if client.has_focus else self.border_normal)
        client.unhide()

    @expose_command()
    def left(self):
        if self.clients.clients:
            self.group.focus(self.focus_previous(self.clients.current_client) or self.focus_last(), warp=False)

    @expose_command()
    def right(self):
        if self.clients.clients:
            self.group.focus(self.focus_next(self.clients.current_client) or self.focus_first(), warp=False)

    @expose_command()
    def up(self): self.left()

    @expose_command()
    def down(self): self.right()

    @expose_command()
    def shuffle_left(self):
        self.clients.shuffle_up(); self.group.layout_all()

    @expose_command()
    def shuffle_right(self):
        self.clients.shuffle_down(); self.group.layout_all()

    @expose_command()
    def shuffle_up(self): self.shuffle_left()

    @expose_command()
    def shuffle_down(self): self.shuffle_right()


def toggle_layout(q):
    q.current_group.setlayout('monadtall' if q.current_layout.name == 'hyrule-scroll' else 'hyrule-scroll')


def panel(name):
    return lazy.spawn(['qs','-c','fatih','ipc','call','desktop',name])


def install(config):
    if not any(l.name == 'hyrule-scroll' for l in config['layouts']):
        config['layouts'].append(HyruleScroll())
    definitions = [
        (['mod4'],'Return',lazy.spawn('kitty'),'Kitty'),
        (['mod4'],'d',panel('launcher'),'Uygulama başlatıcı'),
        (['mod4'],'p',lazy.spawn(['violet-desktop','palette']),'Komut paleti'),
        (['mod4'],'a',panel('toggle'),'Kontrol merkezi'),
        (['mod4'],'n',panel('notifications'),'Bildirim merkezi'),
        (['mod4'],'e',lazy.spawn('nautilus'),'Dosyalar'),
        (['mod4'],'b',lazy.spawn('firefox'),'Firefox'),
        (['mod4'],'m',lazy.spawn('mybrain-python'),'MyBrain'),
        (['mod4'],'i',panel('settings'),'Sistem ayarları'),
        (['mod4'],'k',lazy.spawn(['qs','-c','fatih','ipc','call','desktop','feature','daily']),'Krallığın akışı'),
        (['mod4'],'r',lazy.spawn(['violet-desktop','radial']),'Kalem halkası'),
        (['mod4'],'w',lazy.spawn(['violet-desktop','overview']),'Pencere atlası'),
        (['mod4','shift'],'a',lazy.spawn('violet-agent'),'AI yardımcısı'),
        (['mod4','shift'],'s',lazy.spawn('violet-remote-settings'),'Telegram / SSH alanı'),
        (['mod4','shift'],'n',lazy.spawn(['kitty','nvim']),'Neovim'),
        (['mod4','shift'],'b',lazy.spawn('violet-bazaar'),'Bazaar'),
        (['mod4','control'],'space',lazy.function(toggle_layout),'Yatay kayan / klasik döşeme'),
        # Press Super while Ctrl+Alt are already down (and either order of left/right Super).
        (['control','mod1'],'Super_L',lazy.function(toggle_layout),'Yatay kayan / klasik döşeme'),
        (['control','mod1'],'Super_R',lazy.function(toggle_layout),'Yatay kayan / klasik döşeme'),
    ]
    for superkey in ['Super_L','Super_R']:
        definitions.append((['control','mod1','mod4'],superkey,lazy.function(toggle_layout),'Yatay kayan / klasik döşeme'))
    for key,action in [('Left','left'),('Right','right'),('Up','up'),('Down','down')]:
        definitions.append((['mod4'],key,getattr(lazy.layout,action)(),'Pencere odağı '+action))
        definitions.append((['mod4','shift'],key,getattr(lazy.layout,'shuffle_'+action)(),'Pencereyi taşı '+action))
    identities={(frozenset(m), k.lower()) for m,k,_,_ in definitions}
    config['keys'][:]=[k for k in config['keys'] if (frozenset(k.modifiers),k.key.lower()) not in identities]
    for mods,key,command,label in definitions:
        config['keys'].append(Key(mods,key,command,desc=label))


@hook.subscribe.client_managed
def float_tools(window):
    if (window.name or '').startswith('Violet ·'):
        window.floating=True
        window.center()
