{ config, pkgs, ... }:

{
  imports = [
    ./profiles/desktop.nix
    ./profiles/services.nix
  ];

  home.username = "fatih";
  home.homeDirectory = "/home/fatih";
  home.stateVersion = "26.05";

  programs.home-manager.enable = true;

  programs.bash = {
    enable = true;

    shellAliases = {
      rebuild = "sudo nixos-rebuild build --flake /etc/nixos#nixos && sudo nixos-rebuild switch --flake /etc/nixos#nixos";
      update = "sudo nix flake update --flake /etc/nixos";
      cleanup = "sudo nix-collect-garbage -d";
      ll = "ls -lah";
    };
  };

  programs.git.enable = true;

  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
  };

  home.packages = with pkgs; [
    nix-index
    comma
    cachix
    nh
  ];

  xdg.enable = true;

  xdg.configFile."qtile" = {
    source = ./qtile;
    recursive = true;
  };
}
