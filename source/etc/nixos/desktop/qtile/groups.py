from libqtile.config import Group
groups = [Group(str(i), label=name) for i, name in enumerate(
    ['Kod', 'Web', 'Hukuk', 'Okuma', 'Medya', 'Sohbet', 'Sistem', '8', '9'], 1)]
