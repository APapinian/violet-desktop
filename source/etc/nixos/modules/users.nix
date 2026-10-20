{ ... }:

{
users.users.fatih = {
    isNormalUser = true;
    description = "Fatih";

    extraGroups = [
      "wheel"
      "networkmanager"
      "video"
      "audio"
      "input"
    ];
  };
}
