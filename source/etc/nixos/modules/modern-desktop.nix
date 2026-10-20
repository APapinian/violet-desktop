{ config, lib, pkgs, ... }:
{
  environment.systemPackages = with pkgs; [ nautilus loupe papers gnome-text-editor
    sushi file-roller gnome-disk-utility adwaita-icon-theme galaxy-buds-client ];
  programs.kdeconnect.enable = true;
  services.dbus.packages = [ pkgs.sushi pkgs.kdePackages.kdeconnect-kde ];
  services.gvfs.enable = true;
  services.udisks2.enable = true;
  services.tumbler.enable = true;
  services.flatpak.enable = true;
  programs.appimage = { enable = true; binfmt = true; };
  hardware.bluetooth = {
    enable = true;
    powerOnBoot = true;
    settings.General.Experimental = true;
  };
  services.blueman.enable = true;
  services.pipewire = {
    enable = lib.mkDefault true;
    pulse.enable = lib.mkDefault true;
    wireplumber.enable = lib.mkDefault true;
    wireplumber.extraConfig."70-violet-buds" = {
      "monitor.bluez.rules" = [{
        matches = [{ "device.description" = "~.*[Bb]uds.*"; }];
        actions.update-props = {
          "bluez5.auto-connect" = [ "a2dp_sink" "hfp_hf" ];
        };
      }];
    };
  };
  xdg.portal = {
    enable = lib.mkDefault true;
    extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
    config.qtile = { default = [ "gtk" ]; "org.freedesktop.impl.portal.ScreenCast" = [ "wlr" ];
      "org.freedesktop.impl.portal.Screenshot" = [ "wlr" ]; };
  };
}
