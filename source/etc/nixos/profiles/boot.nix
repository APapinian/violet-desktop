{ ... }: {
  imports = [
    ../modules/boot.nix
    ../modules/grub-enable.nix
    ../modules/login-theme.nix
    ../modules/hyrule-boot-storage.nix
    ../modules/violet-v6-boot.nix
  ];
}
