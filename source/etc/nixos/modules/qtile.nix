{ pkgs, unstablePkgs, ... }:

{
services.xserver.enable = true;

  services.displayManager.sddm.enable = true;

  # Şimdilik kurtarma masaüstümüz.
  services.desktopManager.plasma6.enable = true;

  services.xserver.xkb = {
    layout = "tr";
    variant = "";
  };

  services.xserver.windowManager.qtile = {
  enable = true;
  # YOGA_NATIVE_TOUCH_V1
  package =
    let baseQtile = unstablePkgs.python3Packages.qtile;
    in assert baseQtile.version == "0.37.1";
    baseQtile.overrideAttrs (old: {
      patches = (old.patches or []) ++ [ ./patches/qtile-yoga-touch.patch ./patches/qtile-yoga-pen.patch ./patches/qtile-violet-pen-menu.patch ./patches/qtile-violet-switcher.patch ];
      passthru = (old.passthru or {}) // {
        yogaTouchPatchRevision = "pr5882-2be9c0b-yoga-v1";
        yogaPenPatchRevision = "yoga-tablet-v2-v1";
      };
    });
  };

  # XWayland
  programs.xwayland.enable = true;
xdg.portal = {
    enable = true;

    extraPortals = with pkgs; [
      xdg-desktop-portal-gtk
      xdg-desktop-portal-wlr
    ];
  };
}
