{
  description = "CEGIW development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfreePredicate = pkg: nixpkgs.lib.getName pkg == "nuxmv";
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python313
            pkgs.gcc
            pkgs.expect
            pkgs.spin
            pkgs.nuxmv
          ];

          SPIN_PATH = "${pkgs.spin}/bin/spin";
          NUXMV_PATH = "${pkgs.nuxmv}/bin/nuXmv";
          GCC_PATH = "${pkgs.gcc}/bin/gcc";

          shellHook = ''
            if [ ! -d .venv ]; then
              python3 -m venv .venv
            fi
            source .venv/bin/activate
            pip install -q -r dev-requirements.txt
          '';
        };
      });
}
