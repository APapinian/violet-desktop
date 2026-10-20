{ ... }: {
  imports = [ ./profiles/hardware.nix ./profiles/boot.nix ./profiles/services.nix ./profiles/desktop.nix ];
  system.stateVersion = "26.05";
}
