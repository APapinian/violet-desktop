{ config, pkgs, ... }:
let
  status = pkgs.writeShellScriptBin "fatih-shell-status" ''
    export PATH=${pkgs.lib.makeBinPath [ pkgs.wireplumber pkgs.networkmanager pkgs.playerctl pkgs.power-profiles-daemon ]}:$PATH
    exec ${pkgs.python3}/bin/python3 ${./shell/status.py} "$@"
  '';
  start = pkgs.writeShellScriptBin "fatih-desktop-start" ''
    # Qtile oturum bilgisini D-Bus ve systemd kullanıcı servislerine aktar.
    export XDG_CURRENT_DESKTOP=qtile
    if [ -n "''${WAYLAND_DISPLAY:-}" ]; then
      export XDG_SESSION_TYPE=wayland
    else
      export XDG_SESSION_TYPE=x11
    fi
    ${pkgs.dbus}/bin/dbus-update-activation-environment --systemd \
      DISPLAY WAYLAND_DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE
    # HYRULE_USB_SESSION_V1
    ${pkgs.systemd}/bin/systemctl --user start --no-block violet-polkit-agent.service udiskie.service
    ${pkgs.systemd}/bin/systemctl --user start --no-block \
      violet-desktop.service violet-kdeconnect.service violet-buds-client.service \
      syncthing.service fatih-kingdom.service fatih-clipboard.service
    ${pkgs.quickshell}/bin/qs -c fatih -d
  '';
in {
  home.packages = with pkgs; [
    quickshell rofi foot rubik nerd-fonts.caskaydia-cove
    brightnessctl wireplumber playerctl networkmanager
    blueman pavucontrol mako power-profiles-daemon status start
  ];
  xdg.configFile."quickshell/fatih" = {
    source = ./shell;
    recursive = true;
  };
  xdg.configFile."rofi/config.rasi".text = ''
    @theme "${./launcher.rasi}"
  '';
  xdg.configFile."foot/foot.ini".text = ''
    [main]
    font=CaskaydiaCove Nerd Font:size=11
    pad=18x18
    [colors-dark]
    background=17151f
    foreground=ece4f8
    regular0=302c3c
    regular1=ffb4ab
    regular2=b8dbbc
    regular3=f2d49c
    regular4=b9c7ff
    regular5=c5b4ff
    regular6=a5d6db
    regular7=ece4f8
    bright0=847991
    bright1=ffc8c2
    bright2=cbeacc
    bright3=ffe3af
    bright4=d0d9ff
    bright5=ddceff
    bright6=bce9ec
    bright7=ffffff
  '';
}
