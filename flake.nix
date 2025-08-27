{
  description = "kontrol-node - A local testnet node powered by KEVM";
  inputs = {
    rv-nix-tools.url = "github:runtimeverification/rv-nix-tools/854d4f05ea78547d46e807b414faad64cea10ae4";
    nixpkgs.follows = "rv-nix-tools/nixpkgs";

    kontrol.url = "github:runtimeverification/kontrol/v1.0.183";
    kontrol.inputs.nixpkgs.follows = "nixpkgs";

    k-framework.follows = "kontrol/k-framework";
    k-framework.inputs.nixpkgs.follows = "nixpkgs";

    flake-utils.url = "github:numtide/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix/680e2f8e637bc79b84268949d2f2b2f5e5f1d81c";
    # stale nixpkgs is missing the alias `lib.match` -> `builtins.match`
    # therefore point uv2nix to a patched nixpkgs, which introduces this alias
    # this is a temporary solution until nixpkgs us up-to-date again
    uv2nix.inputs.nixpkgs.url = "github:runtimeverification/nixpkgs/libmatch";
    # inputs.nixpkgs.follows = "nixpkgs";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs/7dba6dbc73120e15b558754c26024f6c93015dd7";
    pyproject-build-systems = {
      inputs.nixpkgs.follows = "uv2nix/nixpkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "uv2nix/pyproject-nix";
    };
    pyproject-nix.follows = "uv2nix/pyproject-nix";
  };
  outputs = { self, rv-nix-tools, nixpkgs, kontrol, k-framework, flake-utils, pyproject-nix, pyproject-build-systems, uv2nix }:
  let
    pythonVer = "310";
  in flake-utils.lib.eachSystem [
      "x86_64-linux"
      "x86_64-darwin"
      "aarch64-linux"
      "aarch64-darwin"
    ] (system:
    let
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
          uvOverlay
          kOverlay
          kontrol-nodeOverlay
        ];
      };
      python = pkgs."python${pythonVer}";
    in {
      devShells.default = pkgs.mkShell {
        name = "uv develop shell";
        buildInputs = [
          python
        ] ++ (with pkgs; [
          uv
          k.openssl.secp256k1
          openssl.dev
          secp256k1
          pkg-config
          mpfr
          cmake
          boost
        ]);
        env = {
          # prevent uv from managing Python downloads and force use of specific
          UV_PYTHON_DOWNLOADS = "never";
          UV_PYTHON = python.interpreter;
        };
        shellHook = ''
          unset PYTHONPATH
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
