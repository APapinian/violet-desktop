{ pkgs, ... }:

{
programs.firefox.enable = true;

  programs.git.enable = true;

  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
  };
environment.systemPackages = with pkgs; [
    # Editors
    vim
    nano
    micro
    neovim

    # CLI
    git
    curl
    wget
    unzip
    p7zip

    # Monitoring
    htop
    btop
    fastfetch

    # Hardware/debug
    pciutils
    usbutils

    # GUI
    gparted

    # Qtile essentials
    foot
    rofi
    dunst
    brightnessctl

    # Wayland tools
    wl-clipboard
    grim
    slurp

    # Audio
    pavucontrol

    # Bluetooth
    blueman
  ];
}
