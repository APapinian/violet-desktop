{ pkgs, ... }:
let
  diagnose = pkgs.writeShellScriptBin "yoga-diagnose" ''
    export PATH=${pkgs.lib.makeBinPath [ pkgs.coreutils pkgs.procps pkgs.util-linux pkgs.systemd pkgs.pciutils ]}:$PATH
    exec ${pkgs.bash}/bin/bash ${./scripts/yoga-diagnose}
  '';
in {
  home.packages = [ diagnose ];
}
