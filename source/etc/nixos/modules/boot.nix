{ pkgs, ... }:

{
boot.loader.systemd-boot.enable = true;
  boot.loader.timeout = 2;
  boot.loader.efi.canTouchEfiVariables = true;

  # İlk aşamada latest kernel.
  # Sistem oturduktan sonra Zen kernel'i ayrıca deneyeceğiz.
  boot.kernelPackages = pkgs.linuxPackages_latest;
}
