{ lib, ... }: {
  services.openssh = {
    enable = true;
    openFirewall = false;
    settings = {
      PasswordAuthentication = lib.mkForce false;
      KbdInteractiveAuthentication = lib.mkForce false;
      PermitRootLogin = lib.mkForce "no";
      AllowUsers = [ "fatih" ];
    };
  };
  # Add authorized public keys here; do not put private keys or bot tokens in Nix.
  users.users.fatih.openssh.authorizedKeys.keys = [ ];
}
