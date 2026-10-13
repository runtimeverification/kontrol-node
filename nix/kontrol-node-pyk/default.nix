{
  lib,
  callPackage,

  pyproject-nix,
  pyproject-build-systems,
  kontrol-node-pyproject,
  pyproject-overlays ? [ ],

  python
}:
let
  inherit (kontrol-node-pyproject) lockFileOverlay workspace;

  pyproject-util = callPackage pyproject-nix.build.util {};
  pyproject-packages = callPackage pyproject-nix.build.packages {
    inherit python;
  };

  buildSystemsOverlay = import ./build-systems-overlay.nix;

  # construct package set
  pythonSet = pyproject-packages.overrideScope (lib.composeManyExtensions ([
    # make build tools available by default as these are not necessarily specified in python lock files
    pyproject-build-systems.overlays.default
    # include all packages from the python lock file
    lockFileOverlay
    # add build system overrides to certain python packages
    buildSystemsOverlay
  ] ++ pyproject-overlays));
in pyproject-util.mkApplication {
  # default dependancy group enables no optional dependencies and no dependency-groups
  venv = pythonSet.mkVirtualEnv "kontrol-node-env" workspace.deps.default;
  package = pythonSet.kontrol-node;
}
