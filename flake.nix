{
  description = "kontrol-node - A local testnet node powered by KEVM";
  inputs = {
    rv-nix-tools.url = "github:runtimeverification/rv-nix-tools/854d4f05ea78547d46e807b414faad64cea10ae4";
    nixpkgs.follows = "rv-nix-tools/nixpkgs";

    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    kontrol.url = "github:runtimeverification/kontrol/v1.0.172";
    kontrol.inputs.nixpkgs.follows = "nixpkgs";
    k-framework.follows = "kontrol/k-framework";
  };
  outputs = { self, rv-nix-tools, nixpkgs, nixpkgs-unstable, flake-utils, kontrol, k-framework }:
    flake-utils.lib.eachSystem [
      "x86_64-linux"
      "x86_64-darwin"
      "aarch64-linux"
      "aarch64-darwin"
    ] (system:
      let
        pkgs-unstable = import nixpkgs-unstable {
          inherit system;
        };
        kOverlay = final: prev: {
          k = k-framework.packages.${system}.k;
        };
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            kOverlay
          ];
        };
      in rec {
        devShells.default = pkgs.mkShell {
          name = "poetry develop shell";
          packages = with pkgs; [
            pkgs-unstable.poetry
            python310
            k.openssl.secp256k1
            openssl.dev
            secp256k1
            pkg-config
            mpfr
            cmake
            boost
            clang
          ];
        };
      }
    );
}
