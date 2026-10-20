from libqtile import bar, hook, layout, widget
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
from libqtile.backend.wayland import InputConfig


mod = "mod4"
terminal = "foot"


# ------------------------------------------------------------
# KEYS
# ------------------------------------------------------------

keys = [
    Key([mod], "Return", lazy.spawn(terminal)),
    Key([mod], "d", lazy.spawn("rofi -show drun")),

    Key([mod], "q", lazy.window.kill()),

    Key([mod, "control"], "r", lazy.reload_config()),
    Key([mod, "control"], "q", lazy.shutdown()),

    Key([mod], "h", lazy.layout.left()),
    Key([mod], "l", lazy.layout.right()),
    Key([mod], "j", lazy.layout.down()),
    Key([mod], "k", lazy.layout.up()),

    Key([mod, "shift"], "h", lazy.layout.shuffle_left()),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right()),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up()),

    Key([mod], "space", lazy.next_layout()),

    Key(
        [],
        "XF86AudioRaiseVolume",
        lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+"),
    ),

    Key(
        [],
        "XF86AudioLowerVolume",
        lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),
    ),

    Key(
        [],
        "XF86AudioMute",
        lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),
    ),

    Key(
        [],
        "XF86MonBrightnessUp",
        lazy.spawn("brightnessctl set +5%"),
    ),

    Key(
        [],
        "XF86MonBrightnessDown",
        lazy.spawn("brightnessctl set 5%-"),
    ),
]


# ------------------------------------------------------------
# GROUPS
# ------------------------------------------------------------

groups = [
    Group("1", label="DEV"),
    Group("2", label="WEB"),
    Group("3", label="LAW"),
    Group("4", label="READ"),
    Group("5", label="MEDIA"),
    Group("6", label="CHAT"),
    Group("7", label="SYS"),
    Group("8"),
    Group("9"),
]


for group in groups:
    keys.extend(
        [
            Key(
                [mod],
                group.name,
                lazy.group[group.name].toscreen(),
            ),

            Key(
                [mod, "shift"],
                group.name,
                lazy.window.togroup(group.name),
            ),
        ]
    )


# ------------------------------------------------------------
# LAYOUT
# ------------------------------------------------------------

layout_theme = {
    "border_width": 2,
    "margin": 8,
}

layouts = [
    layout.MonadTall(**layout_theme),
    layout.Max(),
    layout.Columns(**layout_theme),
]


# ------------------------------------------------------------
# WIDGETS
# ------------------------------------------------------------

def widgets():
    return [
        widget.GroupBox(),
        widget.Sep(),

        widget.WindowName(),

        widget.Systray(),

        widget.Wlan(
            interface="wlp2s0",
            format="{essid}",
        ),

        widget.Volume(),

        widget.Battery(
            format="{char} {percent:2.0%}",
        ),

        widget.Clock(
            format="%d.%m.%Y  %H:%M",
        ),
    ]


# ------------------------------------------------------------
# SCREEN
# ------------------------------------------------------------

screens = [
    Screen(
        top=bar.Bar(
            widgets(),
            32,
        ),
    )
]


# ------------------------------------------------------------
# MOUSE
# ------------------------------------------------------------

mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),

    Drag(
        [mod],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
    ),

    Click(
        [mod],
        "Button2",
        lazy.window.bring_to_front(),
    ),
]


# ------------------------------------------------------------
# FLOATING
# ------------------------------------------------------------

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,

        Match(title="branchdialog"),
        Match(title="pinentry"),
    ]
)


# ------------------------------------------------------------
# GENERAL
# ------------------------------------------------------------

follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"


# ------------------------------------------------------------
# WAYLAND INPUT
# ------------------------------------------------------------

wl_input_rules = {
    # Türkçe Q klavye
    "type:keyboard": InputConfig(
        kb_layout="tr",
    ),

    # Lenovo Yoga touchpad
    "10182:480:GXTP5100:00 27C6:01E0 Touchpad": InputConfig(
        tap=True,
        natural_scroll=False,
        pointer_accel=0.2,
        scroll_method="two_finger",
    ),
}


wmname = "Qtile"
