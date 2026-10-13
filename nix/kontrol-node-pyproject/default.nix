{
  callPackage,

  uv2nix,
}:
let
  # load a uv workspace from a workspace root
  workspace = uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = callPackage ../kontrol-node-source { };
  };

  # create overlay
  lockFileOverlay = workspace.mkPyprojectOverlay {
    # prefer "wheel" over "sdist" due to maintenance overhead
    # there is no bundled set of overlays for "sdist" in uv2nix, in contrast to poetry2nix
    sourcePreference = "wheel";
  };
in {
  inherit lockFileOverlay workspace;
}
