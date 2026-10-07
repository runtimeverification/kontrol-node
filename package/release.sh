#!/usr/bin/env bash
#
# Interactive, local replacement for the former `release.yml` / `update.yml` GitHub workflows.
#
# Everything is built from the local checkout. As with any flake, Nix ignores untracked files.
#
# Steps (each one asks for confirmation before running):
#   1. Create GitHub release `v<package/version>` targeting HEAD.
#   2. Build `kontrol-node` and push its full build closure to the `k-framework` Cachix cache.
#   3. Publish and pin `kontrol-node` in the `k-framework-binary` Cachix cache (what `kup install` uses).
#
# Steps 1 and 3 reference HEAD on GitHub, so they are skipped unless the working tree is clean and
# HEAD is pushed. Step 2 also runs on uncommitted changes.
#
# Credentials are read from the environment, or prompted for (input hidden) when missing:
#   GH_TOKEN                  GitHub token for `gh` (only needed if `gh auth status` fails)
#   CACHIX_SOURCE_TOKEN       Cachix auth token for `k-framework`
#   CACHIX_BINARY_TOKEN  Cachix auth token for `k-framework-binary`
#
# Do NOT run this script with `bash -x`: tracing would print the credentials.

set -euo pipefail

REPO="runtimeverification/kontrol-node"
PACKAGE="${PACKAGE:-kontrol-node}"
KEEP_DAYS="${KEEP_DAYS:-180}"
SOURCE_CACHE="k-framework"
BINARY_CACHE="k-framework-binary"

usage() {
    cat <<EOF
usage: $0 [--yes]

Builds and publishes the local checkout.

  --yes  Run all steps without asking for confirmation.

Environment: GH_TOKEN, CACHIX_SOURCE_TOKEN, CACHIX_BINARY_TOKEN,
             PACKAGE (default: kontrol-node), KEEP_DAYS (default: 180).
EOF
}

notif() { echo -e "\033[1;34m==\033[0m $*" >&2 ; }
warn()  { echo -e "\033[1;33m[WARN]\033[0m $*" >&2 ; }
fatal() { echo -e "\033[1;31m[FATAL]\033[0m $*" >&2 ; exit 1 ; }

ASSUME_YES=false

confirm() {
    local prompt="$1" answer
    if ${ASSUME_YES}; then return 0; fi
    read -rp "${prompt} [Y/n] " answer </dev/tty
    [[ -z "${answer}" || "${answer}" =~ ^[Yy] ]]
}

# Sets the shell variable named $1 from the environment or a hidden prompt. It is deliberately
# not exported: callers hand it only to the single command that needs it.
require_secret() {
    local var="$1" description="$2" value
    if [[ -n "${!var:-}" ]]; then
        notif "Using ${var} from environment."
        return
    fi
    read -rsp "${description} (${var}): " value </dev/tty
    echo >&2
    [[ -n "${value}" ]] || fatal "${var} must not be empty."
    printf -v "${var}" '%s' "${value}"
}

nix_() { nix --extra-experimental-features 'nix-command flakes' "$@" ; }

# Puts tool $1 on PATH, building flake $2 if it is not installed.
ensure_tool() {
    local tool="$1" flake="$2" out
    command -v "${tool}" &>/dev/null && return
    notif "${tool} not found, building ${flake} ..."
    out="$(nix_ build "${flake}" --no-link --print-out-paths | head -n1)"
    export PATH="${out}/bin:${PATH}"
}

# --- Steps ------------------------------------------------------------------------------------

step_github_release() {
    if ! gh auth status &>/dev/null; then
        require_secret GH_TOKEN "GitHub token"
    fi
    local existing
    if existing="$(GH_TOKEN="${GH_TOKEN:-}" gh release view "${TAG}" --repo "${REPO}" --json tagName --jq .tagName 2>/dev/null)"; then
        warn "Release ${existing} already exists, skipping."
        return
    fi
    GH_TOKEN="${GH_TOKEN:-}" gh release create "${TAG}" --repo "${REPO}" --target "${REV}" --title "${TAG}" --notes ''
    notif "Created release ${TAG}."
}

step_source_cache() {
    require_secret CACHIX_SOURCE_TOKEN "Cachix token for ${SOURCE_CACHE}"
    ensure_tool cachix nixpkgs#cachix
    notif "Building ${FLAKE_REF} ..."
    nix_ build "${FLAKE_REF}" --no-link --print-build-logs
    local drv
    drv="$(nix_ path-info --derivation "${FLAKE_REF}")"
    notif "Pushing build closure of ${drv} to ${SOURCE_CACHE} ..."
    nix-store --query --requisites --include-outputs "${drv}" \
        | CACHIX_AUTH_TOKEN="${CACHIX_SOURCE_TOKEN}" cachix push "${SOURCE_CACHE}"
}

step_binary_cache() {
    require_secret CACHIX_BINARY_TOKEN "Cachix token for ${BINARY_CACHE}"
    ensure_tool cachix nixpkgs#cachix
    ensure_tool kup github:runtimeverification/kup
    # kup builds the local directory and pins the result under `github:<origin>/<HEAD>#<package>`.
    notif "Publishing ${FLAKE_REF} to ${BINARY_CACHE} (keep ${KEEP_DAYS} days) ..."
    CACHIX_AUTH_TOKEN="${CACHIX_BINARY_TOKEN}" kup publish --keep-days "${KEEP_DAYS}" "${BINARY_CACHE}" "${FLAKE_REF}"
}

# --- Main -------------------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case "$1" in
        --yes|-y)  ASSUME_YES=true ; shift ;;
        -h|--help) usage ; exit 0 ;;
        *)         usage ; fatal "Unknown argument: $1" ;;
    esac
done

for tool in git gh nix nix-store; do
    command -v "${tool}" &>/dev/null || fatal "Required tool not found: ${tool}"
done

cd "$(git rev-parse --show-toplevel)"

notif "Fetching origin ..."
git fetch --quiet origin

REV="$(git rev-parse HEAD)"
VERSION="$(tr -d '[:space:]' < package/version)"
TAG="v${VERSION}"
FLAKE_REF="${PWD}#${PACKAGE}"
SYSTEM="$(nix_ eval --impure --raw --expr builtins.currentSystem)"

DIRTY=false
STATE="clean"
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    DIRTY=true
    STATE="uncommitted changes (included in the build)"
fi
PUSHED=true
if [[ -z "$(git branch --remotes --contains "${REV}")" ]]; then
    PUSHED=false
    STATE="${STATE}, HEAD not pushed"
fi

cat >&2 <<EOF

  Commit:   ${REV}
            $(git log -1 --format='%s (%an, %ad)' --date=short "${REV}")
  State:    ${STATE}
  Version:  ${VERSION} (tag ${TAG})
  Package:  ${FLAKE_REF}
  System:   ${SYSTEM}  (only this system's binaries are cached; run on other machines for more)

EOF
confirm "Continue with this release?" || fatal "Aborted."

# <function>|<needs a clean, pushed HEAD>|<title>
STEPS=(
    "step_github_release|true|Create GitHub release ${TAG}"
    "step_source_cache|false|Push build closure to the ${SOURCE_CACHE} cache"
    "step_binary_cache|true|Publish ${PACKAGE} to the ${BINARY_CACHE} cache (kup)"
)

for entry in "${STEPS[@]}"; do
    IFS='|' read -r fn needs_published title <<< "${entry}"
    echo >&2
    if ${needs_published} && { ${DIRTY} || ! ${PUSHED}; }; then
        warn "Skipped: ${title} (needs a clean working tree with HEAD pushed to GitHub)"
    elif confirm "${title}?"; then
        notif "${title}"
        "${fn}"
    else
        warn "Skipped: ${title}"
    fi
done

echo >&2
notif "Done."
