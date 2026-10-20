{ config, lib, pkgs, ... }:
let
  themeSource = ../themes/hyrule-violet/plymouth;
  plymouthTheme = pkgs.runCommand "hyrule-violet-plymouth" {} ''
    destination=$out/share/plymouth/themes/hyrule-violet
    mkdir -p "$destination"
    cp ${themeSource}/* "$destination/"
    substituteInPlace "$destination/hyrule-violet.plymouth" \
      --replace-fail '@THEME_DIR@' "$destination"
  '';
  snapshot = pkgs.writeShellApplication {
    name = "violet-home-snapshot";
    runtimeInputs = [ pkgs.btrfs-progs pkgs.coreutils pkgs.util-linux pkgs.findutils ];
    text = builtins.readFile ./hyrule-boot-storage/home-snapshot.sh;
  };
  usbCheck = pkgs.writeShellApplication {
    name = "violet-usb-check";
    runtimeInputs = [ pkgs.util-linux pkgs.systemd pkgs.glib ];
    text = ''
      lsblk -o NAME,TRAN,SIZE,FSTYPE,LABEL,MOUNTPOINTS
      systemctl --user status udiskie.service --no-pager || true
      gio mount -li || true
      journalctl --user -u udiskie.service -b -n 25 --no-pager || true
    '';
  };
in {
  assertions = [
    { assertion = config.fileSystems."/".fsType == "btrfs"
        && config.fileSystems."/home".fsType == "btrfs"
        && config.fileSystems."/nix".fsType == "btrfs";
      message = "Hyrule paketi mevcut /, /home ve /nix Btrfs düzeni içindir."; }
    { assertion = config.boot.loader.grub.enable;
      message = "Hyrule açılış paketi mevcut grub-enable.nix modülünü gerektirir."; }
  ];

  # Existing UUIDs, subvol=home and subvol=nix remain authoritative.
  fileSystems."/".options = lib.mkAfter [ "compress=zstd:3" "noatime" ];
  fileSystems."/home".options = lib.mkAfter [ "compress=zstd:3" "noatime" ];
  fileSystems."/nix".options = lib.mkAfter [ "compress=zstd:3" "noatime" ];
  services.btrfs.autoScrub = {
    enable = true;
    interval = "monthly";
    fileSystems = [ "/" ];
  };
  services.fstrim.enable = true;
  systemd.services.violet-home-snapshot = {
    description = "Hyrule: /home için salt okunur günlük Btrfs anlık görüntüsü";
    requires = [ "home.mount" ];
    after = [ "home.mount" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${snapshot}/bin/violet-home-snapshot";
      Nice = 19;
      IOSchedulingClass = "idle";
    };
  };
  systemd.timers.violet-home-snapshot = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
      RandomizedDelaySec = "15m";
    };
  };

  services.udisks2.enable = true;
  services.gvfs.enable = true;
  security.polkit.enable = true;
  boot.supportedFilesystems.exfat = true;
  environment.systemPackages = [ snapshot usbCheck pkgs.btrfs-progs pkgs.exfatprogs ];
  home-manager.users.fatih = { lib, pkgs, ... }: {
    services.udiskie = {
      enable = true;
      automount = true;
      notify = true;
      tray = "never";
      settings = {
        program_options.file_manager = "${pkgs.nautilus}/bin/nautilus";
        # Keep Ventoy's EFI helper out of the file manager.
        device_config = [ { id_label = "VTOYEFI"; ignore = true; } ];
      };
    };
    # Qtile's desktop starter explicitly starts these after importing its env.
    # This also avoids waiting on a graphical-session target Qtile doesn't start.
    systemd.user.services.udiskie = {
      Unit.After = lib.mkForce [ "dbus.service" ];
      Service = { Restart = "on-failure"; RestartSec = 3; };
    };
    systemd.user.services.violet-polkit-agent = {
      Unit = {
        Description = "Hyrule: disk işlemleri için yetkilendirme penceresi";
        After = [ "dbus.service" ];
        PartOf = [ "graphical-session.target" ];
      };
      Service = {
        ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
        Restart = "on-failure";
        RestartSec = 3;
      };
    };
    dconf.settings."org/gnome/desktop/media-handling" = {
      automount = false; # udiskie owns automount in Qtile.
      automount-open = false;
    };
  };

  # The existing login-theme module packages the updated GRUB source directory.
  boot.loader.timeout = lib.mkForce 6;
  boot.loader.grub.gfxmodeEfi = lib.mkForce "auto";
  boot.loader.grub.gfxpayloadEfi = "keep";
  boot.loader.grub.configurationLimit = lib.mkForce 5;
  boot.plymouth = {
    enable = true;
    theme = "hyrule-violet";
    themePackages = [ plymouthTheme ];
  };
  boot.initrd.systemd.enable = true;
  boot.initrd.verbose = false;
  boot.consoleLogLevel = 3;
  boot.kernelParams = lib.mkAfter [ "quiet" "splash" "rd.systemd.show_status=auto" "rd.udev.log_level=3" ];
  system.build.hyruleVioletPlymouth = plymouthTheme;
}
