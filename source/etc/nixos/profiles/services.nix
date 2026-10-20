{ ... }: {
  imports = [
    ../modules/nix.nix
    ../modules/performance.nix
    ../modules/power.nix
    ../modules/networking.nix
    ../modules/bluetooth.nix
    ../modules/audio.nix
    ../modules/locale.nix
    ../modules/printing.nix
    ../modules/users.nix
    ../modules/violet-v6-remote.nix
  ];
}
