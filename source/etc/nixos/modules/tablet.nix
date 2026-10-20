{ pkgs, ... }:
let readerPython = pkgs.python3.withPackages (ps: [ ps.evdev ]);
in {
  hardware.sensor.iio.enable = true;
  security.pam.services.swaylock = {};
  services.udev.extraRules = ''
    SUBSYSTEM=="input", KERNEL=="event*", ATTRS{name}=="Lenovo Yoga Tablet Mode Control switch", SYMLINK+="input/yoga-tablet-mode", TAG+="systemd", ENV{SYSTEMD_WANTS}+="yoga-tablet-state.service"
  '';
  systemd.services.yoga-tablet-state = {
    description = "Yoga tablet-mode switch state";
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "${readerPython}/bin/python3 ${./tablet-state.py}";
      Restart = "on-failure";
      RestartSec = 2;
      RuntimeDirectory = "yoga-tablet";
      RuntimeDirectoryMode = "0755";
      UMask = "0022";
      NoNewPrivileges = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      PrivateTmp = true;
      DevicePolicy = "closed";
      DeviceAllow = [ "char-input r" ];
      ReadWritePaths = [ "/run/yoga-tablet" ];
      RestrictAddressFamilies = [ "AF_UNIX" ];
    };
  };
  services.xserver.windowManager.qtile.extraPackages = ps: [ ps.qtile-extras ];
}
