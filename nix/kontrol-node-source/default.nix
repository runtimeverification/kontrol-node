{
  lib,
  nix-gitignore
}:

lib.cleanSource (nix-gitignore.gitignoreSourcePure [
    ../../.gitignore
    ".github/"
    "result*"
    "/deps/"
    # do not include submodule directories that might be initilized empty or non-existent due to nix/git
    # otherwise cachix build might not match the version that is requested by `kup`
    # TODO: for new projects, add your submodule directories that are not required for nix builds here!
    # e.g., `"/docs/external-computation"` with `external-computation` being a git submodule directory
    # "/docs/external-computation"
  ] ../../.
)
