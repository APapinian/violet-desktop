{ ... }: {
  imports = [
    ../hardware-configuration.nix
    ../modules/hardware.nix
    ../modules/tablet.nix
  ];
}
