{
  description = "kontrol-node - A local testnet node powered by KEVM";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    k-framework.url = "github:runtimeverification/k/v7.1.267";
    k-framework.inputs.flake-utils.follows = "flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils, k-framework }:
    flake-utils.lib.eachSystem [
      "x86_64-linux"
      "x86_64-darwin"
      "aarch64-linux"
      "aarch64-darwin"
    ] (system:
      let
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
            poetry
            python310
            k.openssl.secp256k1
            openssl.dev
            secp256k1
            pkg-config
            mpfr
            cmake
            boost
          ];
        };
      }
    );
}
