from libqtile import layout
from libqtile.config import Match
theme = dict(border_width=2, margin=12, border_focus='#c5b4ff', border_normal='#302c3c')
layouts = [layout.MonadTall(**theme), layout.Max(), layout.Columns(**theme)]
floating_layout = layout.Floating(
    border_width=2, border_focus='#c5b4ff', border_normal='#302c3c',
    float_rules=[*layout.Floating.default_float_rules,
                 Match(title='branchdialog'), Match(title='pinentry')])
