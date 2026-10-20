{ config, pkgs, ... }:
let
  status = pkgs.writeShellScriptBin "fatih-shell-status" ''
    export PATH=${pkgs.lib.makeBinPath [ pkgs.wireplumber pkgs.networkmanager pkgs.playerctl pkgs.power-profiles-daemon ]}:$PATH
    exec ${pkgs.python3}/bin/python3 ${./quickshell/status.py} "$@"
  '';
  start = pkgs.writeShellScriptBin "fatih-desktop-start" ''
    ${pkgs.quickshell}/bin/qs -c fatih -d
  '';
in {
  home.packages = with pkgs; [
    quickshell rofi foot rubik nerd-fonts.caskaydia-cove
    brightnessctl wireplumber playerctl networkmanager
    blueman pavucontrol mako power-profiles-daemon status start
  ];
  xdg.configFile."quickshell/fatih" = {
    source = ./quickshell;
    recursive = true;
  };
  xdg.configFile."rofi/config.rasi".text = ''
    @theme "${./launcher.rasi}"
  '';
  xdg.configFile."foot/foot.ini".text = ''
    [main]
    font=CaskaydiaCove Nerd Font:size=11
    pad=18x18
    [colors]
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
