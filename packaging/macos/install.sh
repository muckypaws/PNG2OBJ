#!/usr/bin/env bash
# =============================================================================
# packaging/macos/install.sh
# -----------------------------------------------------------------------------
# Copy dist/PNG2OBJ.app into /Applications and (optionally) symlink the CLI
# binary onto the PATH so `png2obj` works from any terminal.
#
# NOTE: macOS-only. Authored for native macOS; not executed on Linux.
#
# Usage:
#   packaging/build_macos.sh        # produce dist/PNG2OBJ.app first
#   packaging/macos/install.sh                 # copy to /Applications + link CLI
#   packaging/macos/install.sh --user          # copy to ~/Applications instead
#   packaging/macos/install.sh --no-cli        # skip the PATH symlink
#   packaging/macos/install.sh --uninstall     # remove app + symlink
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP="${REPO_ROOT}/dist/PNG2OBJ.app"

APPS_DIR="/Applications"
LINK_CLI=1
ACTION="install"
for arg in "$@"; do
    case "${arg}" in
        --user)      APPS_DIR="${HOME}/Applications" ;;
        --no-cli)    LINK_CLI=0 ;;
        --uninstall) ACTION="uninstall" ;;
        -h|--help)   sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "Unknown argument: ${arg}" >&2; exit 2 ;;
    esac
done

APP_DST="${APPS_DIR}/PNG2OBJ.app"
# Binary inside the Nuitka app bundle (CLI executable name is png2obj... but
# Nuitka names it after the entry module; resolve it dynamically at install).
CLI_LINK="/usr/local/bin/png2obj"

if [[ "${ACTION}" == "uninstall" ]]; then
    echo "==> Uninstalling PNG2OBJ"
    rm -rfv "${APP_DST}"
    [[ -L "${CLI_LINK}" ]] && rm -fv "${CLI_LINK}"
    echo "==> Done."
    exit 0
fi

if [[ ! -d "${APP}" ]]; then
    echo "ERROR: ${APP} not found. Run packaging/build_macos.sh first." >&2
    exit 1
fi

echo "==> Installing PNG2OBJ.app into ${APPS_DIR}"
mkdir -p "${APPS_DIR}"
rm -rf "${APP_DST}"
cp -R "${APP}" "${APP_DST}"

if [[ "${LINK_CLI}" -eq 1 ]]; then
    # Find the actual executable inside the bundle.
    BIN="$(find "${APP_DST}/Contents/MacOS" -maxdepth 1 -type f -perm -u+x | head -n1 || true)"
    if [[ -n "${BIN}" ]]; then
        echo "==> Linking CLI: ${CLI_LINK} -> ${BIN}"
        if [[ -w "$(dirname "${CLI_LINK}")" ]]; then
            ln -sf "${BIN}" "${CLI_LINK}"
        else
            echo "    /usr/local/bin not writable; re-run with sudo or add to PATH manually:"
            echo "      sudo ln -sf '${BIN}' '${CLI_LINK}'"
        fi
    else
        echo "WARNING: could not locate the CLI binary inside the bundle." >&2
    fi
fi

echo "==> Done. Launch from Applications, or run: png2obj --help"
