{ config, lib, pkgs, ... }:
let
  # Flatseal is distributed on Flathub; the locked Nixpkgs set has no pkgs.flatseal.
  flatsealLauncher = pkgs.writeShellScriptBin "flatseal" ''
    exec ${pkgs.flatpak}/bin/flatpak run com.github.tchx84.Flatseal "$@"
  '';
  python = pkgs.python3.withPackages (ps: with ps; [ pyqt6 dbus-next psutil pynacl argon2-cffi pillow ]);
  tools = with pkgs; [ playerctl bluez pulseaudio blueman galaxy-buds-client flatpak appimage-run
    nautilus libnotify xdg-utils grim slurp wl-clipboard mako coreutils systemd util-linux
    networkmanager foot nethogs syncthing sushi wf-recorder ffmpeg wlr-randr
    (tesseract.override { enableLanguages = [ "tur" "eng" ]; }) kdePackages.kdeconnect-kde
    flatsealLauncher czkawka pavucontrol ];
  path = lib.makeBinPath tools;
  launcher = name: script: pkgs.writeShellScriptBin name ''
    export PATH="${path}:$PATH"
    export QT_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins:${pkgs.qt6.qtwayland}/lib/qt-6/plugins"
    exec ${python}/bin/python3 ${script} "$@"
  '';
in {
  home.packages = tools ++ [
    (launcher "violetctl" "${./modern}/desktop.py")
    (launcher "mybrain-python" "${./mybrain}/app.py")
    (launcher "violet-appimage" "${./modern}/appimage.py")
    (launcher "violet-desktop" "${./suite}/gui.py")
    (launcher "violet-desktop-daemon" "${./suite}/service.py")
    (launcher "violet-desktop-watch" "${./suite}/watch.py")
    (launcher "violet-desktop-pointer" "${./suite}/pointer.py")
  ];
  xdg.desktopEntries.violet-desktop = {
    name = "Violet Masaüstü"; comment = "Pencereler, kalem, USB, dosyalar ve kurallar";
    exec = "violet-desktop"; icon = "preferences-desktop";
    categories = [ "Settings" "Utility" ]; terminal = false;
  };
  services.syncthing.enable = lib.mkDefault true;
  systemd.user.services.violet-kdeconnect = {
    Unit = { Description = "Violet phone connection"; PartOf = [ "graphical-session.target" ]; };
    Service = { ExecStart = "${pkgs.kdePackages.kdeconnect-kde}/bin/kdeconnectd";
      Restart = "on-failure"; RestartSec = 10; };
  };
  systemd.user.services.violet-desktop = {
    Unit = { Description = "Violet desktop events and status";
      PartOf = [ "graphical-session.target" ]; After = [ "dbus.service" ]; };
    Service = { ExecStart = "${config.home.profileDirectory}/bin/violet-desktop-daemon";
      Restart = "on-failure"; RestartSec = 5; TimeoutStopSec = 15; UMask = "0077"; };
    Install.WantedBy = [ "graphical-session.target" ];
  };
  xdg.mimeApps = {
    enable = true;
    defaultApplications = {
      "inode/directory" = lib.mkForce [ "org.gnome.Nautilus.desktop" ];
      "application/pdf" = [ "org.gnome.Papers.desktop" ];
      "text/plain" = [ "org.gnome.TextEditor.desktop" ];
      "image/jpeg" = [ "org.gnome.Loupe.desktop" ];
      "image/png" = [ "org.gnome.Loupe.desktop" ];
    };
  };
  dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-dark";
  xdg.desktopEntries.mybrain-python = {
    name = "MyBrain"; genericName = "İkinci beyin";
    comment = "Şifreli taşınabilir kasa · Python";
    exec = "mybrain-python"; icon = "accessories-text-editor";
    categories = [ "Office" "Utility" ]; terminal = false;
  };
  xdg.desktopEntries.violet-appimage = {
    name = "AppImage ekle"; exec = "violet-appimage";
    icon = "application-x-executable"; categories = [ "Utility" ]; terminal = false;
  };
  systemd.user.services.violet-buds-client = {
    Unit = { Description = "Galaxy Buds battery and controls"; PartOf = [ "graphical-session.target" ]; };
    Service = { ExecStart = "${pkgs.galaxy-buds-client}/bin/GalaxyBudsClient /StartMinimized";
      Restart = "on-failure"; RestartSec = 15; };
  };
}
