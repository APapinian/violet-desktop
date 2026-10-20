{ pkgs, ... }:

{
  services.power-profiles-daemon.enable = true;

  systemd.services.yoga-power-policy = {
    description = "Yoga adaptör durumuna göre güç profili";
    wantedBy = [ "multi-user.target" ];
    wants = [ "power-profiles-daemon.service" ];
    after = [ "power-profiles-daemon.service" ];
    path = [ pkgs.power-profiles-daemon ];
    environment = {
      YOGA_AC_PROFILE = "performance";
      YOGA_BATTERY_PROFILE = "balanced";
    };
    serviceConfig = {
      Type = "oneshot";
      RuntimeDirectory = "yoga-power-policy";
      RuntimeDirectoryMode = "0700";
      RuntimeDirectoryPreserve = "yes";
      TimeoutStartSec = "15s";
    };
    script = builtins.readFile ./scripts/yoga-power-policy.sh;
  };

  # udev yalnızca kısa, asenkron bir systemd isteği gönderir.
  services.udev.extraRules = ''
    ACTION=="change", SUBSYSTEM=="power_supply", ATTR{type}!="Battery", TEST=="online", RUN+="${pkgs.systemd}/bin/systemctl --no-block start yoga-power-policy.service"
  '';
}
