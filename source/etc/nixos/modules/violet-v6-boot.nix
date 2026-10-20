{ lib, ... }: {
  # Early KMS starts the existing 48-frame Violet Plymouth on the AMD display.
  boot.initrd.kernelModules = lib.mkAfter [ "amdgpu" ];
  boot.loader.grub.gfxpayloadEfi = lib.mkForce "keep";
  # NixOS generates gfxterm from the existing font/theme configuration.
  boot.loader.grub.extraConfig = lib.mkBefore ''
    insmod all_video
    insmod gfxterm
    insmod png
    set color_normal=light-gray/black
    set color_highlight=white/magenta
  '';
}
