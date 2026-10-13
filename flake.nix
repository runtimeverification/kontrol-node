{
  description = "kontrol-node - A local testnet node powered by KEVM";

  inputs = {
    rv-nix-tools.url = "github:runtimeverification/rv-nix-tools/854d4f05ea78547d46e807b414faad64cea10ae4";
    nixpkgs.follows = "rv-nix-tools/nixpkgs";

    kontrol.url = "github:runtimeverification/kontrol/v1.0.213";
    kontrol.inputs.nixpkgs.follows = "nixpkgs";

    kevm.follows = "kontrol/kevm";
    k-framework.follows = "kevm/k-framework";
    flake-utils.follows = "kevm/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix/4cca323a547a1aaa9b94929c4901bed5343eafe8";
    # uv2nix requires a newer version of nixpkgs
    # therefore, we pin uv2nix specifically to a newer version of nixpkgs
    # until we replaced our stale version of nixpkgs with an upstream one as well
    # but also uv2nix requires us to call it with `callPackage`, so we add stuff
    # from the newer nixpkgs to our stale nixpkgs via an overlay
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs-unstable";
    # uv2nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs/042904167604c681a090c07eb6967b4dd4dae88c";
    pyproject-build-systems = {
      inputs.nixpkgs.follows = "uv2nix/nixpkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "uv2nix/pyproject-nix";
    };
    pyproject-nix.follows = "uv2nix/pyproject-nix";
  };
  outputs = {
      self,
      k-framework,
      nixpkgs,
      flake-utils,
      kevm,
      kontrol,
      pyproject-nix,
      pyproject-build-systems,
      uv2nix,
      nixpkgs-unstable,
      ... }:
  let
    pythonVer = "310";
  in flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs-unstable = import nixpkgs-unstable {
        inherit system;
      };
      # for uv2nix, remove this once we updated to a newer version of nixpkgs
      staleNixpkgsOverlay = final: prev: {
        inherit (pkgs-unstable) replaceVars;
      };
      # due to the nixpkgs that we use in this flake being outdated, uv is also heavily outdated
      # we can just use the binary release of uv provided by uv2nix
      uvOverlay = final: prev: {
        uv = uv2nix.packages.${final.system}.uv-bin;
      };
      kontrol-nodeOverlay = final: prev:
      let
        kontrol-node-pyproject = final.callPackage ./nix/kontrol-node-pyproject {
          inherit uv2nix;
        };
        kontrol-node-pyk = final.callPackage ./nix/kontrol-node-pyk {
          inherit pyproject-nix pyproject-build-systems kontrol-node-pyproject;
          pyproject-overlays = [
            (k-framework.overlays.pyk-pyproject system)
            (kevm.overlays.pyk-pyproject system)
            # `kontrol.overlays.pyk-pyproject` overrides `kontrol-pyk`, which is not a python package,
            # so it would leave `kontrol` from `uv.lock` in place; override the right package instead
            (final: prev: {
              inherit (kontrol.packages.${system}.kontrol-pyk-pyproject.lockFileOverlay final prev) kontrol;
            })
          ];
          python = final."python${pythonVer}";
        };
        kontrol-node = final.callPackage ./nix/kontrol-node {
          inherit kontrol-node-pyk;
          rev = self.rev or null;
        };
      in {
        inherit kontrol-node kontrol-node-pyk kontrol-node-pyproject;
      };
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          staleNixpkgsOverlay
          k-framework.overlay
          uvOverlay
          kontrol-nodeOverlay
        ];
      };
      python = pkgs."python${pythonVer}";
    in {
      devShells.default =
      let
        kevmShell = kevm.devShells.${system}.default;
      in pkgs.mkShell {
        # kevm's shell lists K and the build tools in `packages`, which end up in `nativeBuildInputs`
        nativeBuildInputs = kevmShell.nativeBuildInputs;
        buildInputs = kevmShell.buildInputs ++ [
          python
          pkgs.uv
        ];
        env = {
          # prevent uv from managing Python downloads and force use of specific
          UV_PYTHON_DOWNLOADS = "never";
          UV_PYTHON = python.interpreter;
        };
        inherit (kevmShell) shellHook;
      };
      packages = rec {
        inherit (pkgs) kontrol-node kontrol-node-pyk kontrol-node-pyproject;
        default = kontrol-node;
      };
    }) // {
      overlays = {
        default = final: prev: {
          inherit (self.packages.${final.system}) kontrol-node;
        };
        # this pyproject-nix overlay allows for overriding the python packages that are otherwise locked in `uv.lock`
        # by using this overlay in dependant nix flakes, you ensure that nix overrides also override the python package
        pyk-pyproject = system: final: prev: {
          inherit (self.packages.${system}.kontrol-node-pyproject.lockFileOverlay final prev) kontrol-node;
        };
      };
    };
}
