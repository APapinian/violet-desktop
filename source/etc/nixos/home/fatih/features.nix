{ config, lib, pkgs, ... }:
let
  kingdomPython = pkgs.python3.withPackages (ps: with ps; [
    requests feedparser praw ytmusicapi yfinance pulsectl icalendar
    recurring-ical-events syncedlyrics dbus-next twitchapi pyqt6
  ]);
  tools = with pkgs; [ playerctl yt-dlp cliphist wl-clipboard grim slurp
    wlr-randr wvkbd libnotify mako networkmanager blueman foot xdg-utils
    swaylock systemd config.programs.mpv.finalPackage ];
  binPath = lib.makeBinPath tools;
  kingdomctl = pkgs.writeShellScriptBin "kingdomctl" ''
    export PATH="${binPath}:$PATH"
    exec ${kingdomPython}/bin/python3 ${./kingdom}/service.py "$@"
  '';
  overlay = pkgs.writeShellScriptBin "kingdom-overlay" ''
    exec ${pkgs.quickshell}/bin/qs -c fatih ipc call desktop nowPlaying
  '';
in {
  home.packages = [ kingdomctl overlay ] ++ tools;
  programs.mpv = {
    enable = true;
    scripts = [ pkgs.mpvScripts.mpris ];
  };
  xdg.configFile."fatih-kingdom/defaults.json".source = ./kingdom/defaults.json;
  xdg.configFile."fatih-kingdom/secrets.env.example".source = ./kingdom/secrets.env.example;
  systemd.user.services.fatih-kingdom = {
    Unit = {
      Description = "Fatih Kingdom desktop providers";
      PartOf = [ "graphical-session.target" ];
    };
    Service = {
      Type = "simple";
      ExecStart = "${kingdomctl}/bin/kingdomctl serve";
      EnvironmentFile = [ "-%h/.config/fatih-kingdom/secrets.env" ];
      Environment = [ "PATH=${binPath}:/etc/profiles/per-user/${config.home.username}/bin:${config.home.homeDirectory}/.nix-profile/bin:/run/current-system/sw/bin" ];
      Restart = "on-failure";
      RestartSec = 3;
      TimeoutStopSec = 8;
      UMask = "0077";
      NoNewPrivileges = true;
    };
  };
  systemd.user.services.fatih-clipboard = {
    Unit = { Description = "Kingdom text clipboard history"; PartOf = [ "graphical-session.target" ]; };
    Service = {
      ExecStart = "${pkgs.wl-clipboard}/bin/wl-paste --type text --watch ${pkgs.cliphist}/bin/cliphist store";
      Restart = "on-failure";
      RestartSec = 3;
      UMask = "0077";
    };
  };
}
