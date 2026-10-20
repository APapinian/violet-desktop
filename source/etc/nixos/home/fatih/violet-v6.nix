{ config, lib, pkgs, ... }:
let
  python = pkgs.python3.withPackages (ps: [ ps.pyqt6 ]);
  dependencies = with pkgs; [ kitty neovim fastfetch firefox nautilus flatpak playerctl
    wireplumber brightnessctl systemd openssh coreutils quickshell ];
  launch = name: mode: pkgs.writeShellScriptBin name ''
    export PATH="${lib.makeBinPath dependencies}:$PATH"
    export QT_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins:${pkgs.qt6.qtwayland}/lib/qt-6/plugins"
    exec ${python}/bin/python3 ${./v6}/apps.py ${mode} "$@"
  '';
  bazaar = pkgs.writeShellScriptBin "violet-bazaar" ''
    exec ${pkgs.flatpak}/bin/flatpak run io.github.kolunmi.Bazaar "$@"
  '';
  bazaarInstall = pkgs.writeShellScriptBin "violet-bazaar-install" ''
    set -e
    ${pkgs.flatpak}/bin/flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    ${pkgs.flatpak}/bin/flatpak install --user -y flathub io.github.kolunmi.Bazaar
  '';
  intro = pkgs.writeShellScriptBin "violet-terminal-intro" ''
    exec ${pkgs.python3}/bin/python3 ${./v6}/terminal_intro.py
  '';
  firefoxTheme = pkgs.writeShellScriptBin "violet-firefox-theme" ''
    exec ${pkgs.python3}/bin/python3 ${./v6}/firefox_theme.py ${./v6/userChrome.css} ${./v6/userContent.css}
  '';
in {
  home.packages = dependencies ++ [ (launch "violet-agent" "")
    (launch "violet-remote-settings" "remote") (launch "violet-telegram" "bot")
    bazaar bazaarInstall intro firefoxTheme pkgs.papirus-icon-theme ];
  home.sessionVariables = { TERMINAL = "kitty"; EDITOR = "nvim"; VISUAL = "nvim"; };
  programs.bash.initExtra = lib.mkAfter ''
    if [[ $- == *i* && "''${TERM:-}" == xterm-kitty && -z "''${VIOLET_INTRO_DONE:-}" ]]; then
      export VIOLET_INTRO_DONE=1
      violet-terminal-intro
      fastfetch --config "$HOME/.config/fastfetch/config.jsonc"
    fi
  '';
  xdg.configFile."kitty/kitty.conf".source = ./v6/kitty.conf;
  xdg.configFile."nvim/init.lua".source = ./v6/init.lua;
  xdg.configFile."fastfetch/config.jsonc".source = ./v6/fastfetch.json;
  xdg.configFile."fastfetch/link.txt".source = ./v6/link.txt;
  # GTK 4/libadwaita (Nautilus), with GTK 3 fallback.
  xdg.configFile."gtk-4.0/gtk.css".text = builtins.readFile ./v6/gtk.css;
  xdg.configFile."gtk-3.0/gtk.css".text = builtins.readFile ./v6/gtk.css;
  dconf.settings."org/gnome/desktop/interface" = {
    color-scheme = "prefer-dark";
    icon-theme = "Papirus-Dark";
  };
  home.activation.violetV6Defaults = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    $DRY_RUN_CMD ${pkgs.python3}/bin/python3 ${./v6}/migrate.py
  '';
  # Preserve every existing Firefox profile and its userChrome rules.
  home.activation.violetFirefox = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    $DRY_RUN_CMD ${firefoxTheme}/bin/violet-firefox-theme
  '';
  xdg.desktopEntries.violet-agent = { name="Violet AI";exec="violet-agent";icon="system-search";categories=[ "Utility" ]; };
  xdg.desktopEntries.violet-remote = { name="Violet Telegram / SSH";exec="violet-remote-settings";icon="network-server";categories=[ "Settings" ]; };
  xdg.desktopEntries.violet-bazaar = { name="Bazaar";exec="violet-bazaar";icon="io.github.kolunmi.Bazaar";categories=[ "System" ]; };
  xdg.configFile."systemd/user/violet-telegram.service".text = ''
    [Unit]
    Description=Violet Telegram remote control
    After=network-online.target
    [Service]
    ExecStart=${config.home.profileDirectory}/bin/violet-telegram
    Restart=on-failure
    RestartSec=15
    UMask=0077
    NoNewPrivileges=true
    [Install]
    WantedBy=default.target
  '';
}
