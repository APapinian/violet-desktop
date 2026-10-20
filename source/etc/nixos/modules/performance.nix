{ ... }:

{
zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 50;
    priority = 100;
  };

  # Disk swap'ını hardware-configuration.nix üzerinden koruyoruz.
}
