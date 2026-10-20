{ config, lib, pkgs, ... }:
let
  assets = ../themes/hyrule-violet/assets;
  sddmTheme = pkgs.runCommand "hyrule-violet-sddm" { } ''
    mkdir -p $out/share/sddm/themes/hyrule-violet/assets
    cp ${../themes/hyrule-violet/sddm}/* $out/share/sddm/themes/hyrule-violet/
    cp ${assets}/background.png ${assets}/DejaVuSerif.ttf $out/share/sddm/themes/hyrule-violet/assets/
  '';
  grubTheme = pkgs.runCommand "hyrule-violet-grub" {
    nativeBuildInputs = [ pkgs.grub2 ];
  } ''
    mkdir -p $out
    cp ${../themes/hyrule-violet/grub}/* $out/
    cp ${assets}/background.png $out/
    grub-mkfont -s 40 -o $out/serif-40.pf2 ${assets}/DejaVuSerif.ttf
    grub-mkfont -s 18 -o $out/sans-18.pf2 ${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSans.ttf
    grub-mkfont -s 20 -o $out/sans-20.pf2 ${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSans.ttf
    grub-mkfont -s 16 -o $out/sans-16.pf2 ${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSans.ttf
    grub-mkfont -s 16 -o $out/mono-16.pf2 ${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSansMono.ttf
  '';
  previewSddm = config.services.displayManager.sddm.package.override (old: {
    extraPackages = (old.extraPackages or [ ]) ++ config.services.displayManager.sddm.extraPackages;
  });
  preview = pkgs.writeShellScriptBin "hyrule-login-preview" ''
    export QT_QUICK_CONTROLS_STYLE=Basic
    exec ${previewSddm}/bin/sddm-greeter-qt6 --test --theme ${sddmTheme}/share/sddm/themes/hyrule-violet "$@"
  '';
in {
  assertions = [ {
    assertion = config.services.displayManager.sddm.enable;
    message = "Hyrule Violet mevcut SDDM içindir; başka display manager etkinleştirmez.";
  } ];
  services.displayManager.sddm = {
    theme = lib.mkForce "${sddmTheme}/share/sddm/themes/hyrule-violet";
    extraPackages = [ pkgs.qt6.qtdeclarative ];
  };
  # Applying the theme must not terminate the running Qtile session.
  systemd.services.display-manager.restartIfChanged = lib.mkForce false;
  environment.systemPackages = [ sddmTheme preview ];
  environment.etc."hyrule-violet/grub".source = grubTheme;
  # Theme follows the boot loader enabled by the existing configuration.
  boot.loader.grub.theme = lib.mkIf config.boot.loader.grub.enable (lib.mkForce "${grubTheme}");
  system.build.hyruleVioletSddm = sddmTheme;
  system.build.hyruleVioletPreview = preview;
}
