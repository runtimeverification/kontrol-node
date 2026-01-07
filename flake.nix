{
  description = "kontrol-node - A local testnet node powered by KEVM";
  inputs = {
    rv-nix-tools.url = "github:runtimeverification/rv-nix-tools/854d4f05ea78547d46e807b414faad64cea10ae4";
    nixpkgs.follows = "rv-nix-tools/nixpkgs";

    kontrol.url = "github:runtimeverification/kontrol/v1.0.213";
    kontrol.inputs.nixpkgs.follows = "nixpkgs";

    k-framework.follows = "kontrol/k-framework";
    k-framework.inputs.nixpkgs.follows = "nixpkgs";

    flake-utils.url = "github:numtide/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix/4cca323a547a1aaa9b94929c4901bed5343eafe8";
    # uv2nix requires a newer version of nixpkgs
    # therefore, we pin uv2nix specifically to a newer version of nixpkgs
    # until we replaced our stale version of nixpkgs with an upstream one as well
    # but also uv2nix requires us to call it with `callPackage`, so we add stuff
    # from the newer nixpkgs to our stale nixpkgs via an overlay
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs-unstable";
    # uv2nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs/dbfc0483b5952c6b86e36f8b3afeb9dde30ea4b5";
    pyproject-build-systems = {
      inputs.nixpkgs.follows = "uv2nix/nixpkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "uv2nix/pyproject-nix";
    };
    pyproject-nix.follows = "uv2nix/pyproject-nix";
  };
  outputs = { self, rv-nix-tools, nixpkgs, kontrol, k-framework, flake-utils, pyproject-nix, pyproject-build-systems, uv2nix, nixpkgs-unstable }:
  let
    pythonVer = "310";
    nixLibs = pkgs: with pkgs; "-I${openssl.dev}/include -L${openssl.out}/lib -I${secp256k1}/include -L${secp256k1}/lib";
  in flake-utils.lib.eachSystem [
      "x86_64-linux"
      "x86_64-darwin"
      "aarch64-linux"
      "aarch64-darwin"
    ] (system:
    let
      pkgs-unstable = import nixpkgs-unstable {
        inherit system;
      };
      # for uv2nix, remove this once we updated to a newer version of nixpkgs
      staleNixpkgsOverlay = final: prev: {
        inherit (pkgs-unstable) replaceVars;
      };
      # due to the nixpkgs that we use in this flake being outdated, uv is also heavily outdated
      # we can instead use the binary release of uv provided by uv2nix for now
      uvOverlay = final: prev: {
        uv = uv2nix.packages.${final.system}.uv-bin;
      };
      kOverlay = final: prev: {
        k = k-framework.packages.${system}.k;
      };
      kontrol-nodeOverlay = final: prev: {
        kontrol-node = final.callPackage ./nix/kontrol-node {
          inherit pyproject-nix pyproject-build-systems uv2nix;
          python = final."python${pythonVer}";
        };
      };
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          staleNixpkgsOverlay
          uvOverlay
          kOverlay
          kontrol-nodeOverlay
        ];
      };
      python = pkgs."python${pythonVer}";
    in {
      devShells.default = pkgs.mkShell {
        name = "uv develop shell";
        packages = with pkgs; ([
          k
          autoconf
          automake
          cmake
          pkg-config
          python
          clang
          uv
          which
        ] ++ lib.optionals (!stdenv.isDarwin) [
          elfutils
        ]);
        buildInputs = with pkgs; [
          fmt
          libtool
          mpfr
          openssl
          secp256k1
          boost
        ];
        env = {
          # prevent uv from managing Python downloads and force use of specific
          UV_PYTHON_DOWNLOADS = "never";
          UV_PYTHON = python.interpreter;
        };
        shellHook = ''
          export NIX_LIBS="${nixLibs pkgs}"
          unset PYTHONPATH
        '' + pkgs.lib.strings.optionalString (pkgs.stdenv.isAarch64 && pkgs.stdenv.isDarwin) ''
          export APPLE_SILICON=true
        '';
      };
      packages = rec {
        inherit (pkgs) kontrol-node;
        default = kontrol-node;
      };
    }) // {
      overlays.default = final: prev: {
        inherit (self.packages.${final.system}) kontrol-node;
      };
    };
}
