#!/usr/bin/env bash
# =============================================================================
# packaging/linux/install.sh
# -----------------------------------------------------------------------------
# Install the standalone PNG2OBJ Linux binary for the current user (or
# system-wide with --system), including a .desktop entry and icon.
#
# By default installs to ~/.local (no root needed):
#   binary  -> ~/.local/bin/png2obj
#   desktop -> ~/.local/share/applications/png2obj.desktop
#   icon    -> ~/.local/share/icons/hicolor/256x256/apps/png2obj.png
#
# With --system (needs sudo/root): installs under /usr/local and
# /usr/share.
#
# Usage:
#   packaging/build_linux.sh                 # produce dist/png2obj first
#   packaging/linux/install.sh               # per-user install
#   sudo packaging/linux/install.sh --system # system-wide install
#   packaging/linux/install.sh --uninstall   # remove a per-user install
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BINARY="${REPO_ROOT}/dist/png2obj"
ICON="${REPO_ROOT}/packaging/assets/png2obj.png"
DESKTOP="${SCRIPT_DIR}/PNG2OBJ.desktop"

MODE="user"
ACTION="install"
for arg in "$@"; do
    case "${arg}" in
        --system)    MODE="system" ;;
        --uninstall) ACTION="uninstall" ;;
        -h|--help)
            sed -n '2,30p' "${BASH_SOURCE[0]}"
            exit 0 ;;
        *)
            echo "Unknown argument: ${arg}" >&2; exit 2 ;;
    esac
done

if [[ "${MODE}" == "system" ]]; then
    PREFIX="/usr/local"
    SHARE="/usr/share"
else
    PREFIX="${HOME}/.local"
    SHARE="${HOME}/.local/share"
fi

BIN_DST="${PREFIX}/bin/png2obj"
DESKTOP_DST="${SHARE}/applications/png2obj.desktop"
ICON_DST="${SHARE}/icons/hicolor/256x256/apps/png2obj.png"

# Refresh the desktop database if the helper exists (best-effort).
refresh_desktop_db() {
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "${1}" 2>/dev/null || true
    fi
}

if [[ "${ACTION}" == "uninstall" ]]; then
    echo "==> Uninstalling PNG2OBJ (${MODE})"
    rm -fv "${BIN_DST}" "${DESKTOP_DST}" "${ICON_DST}"
    refresh_desktop_db "${SHARE}/applications"
    echo "==> Done."
    exit 0
fi

# --- Install ----------------------------------------------------------------
if [[ ! -f "${BINARY}" ]]; then
    echo "ERROR: ${BINARY} not found. Run packaging/build_linux.sh first." >&2
    exit 1
fi

echo "==> Installing PNG2OBJ (${MODE}) into ${PREFIX}"
install -D -m 0755 "${BINARY}" "${BIN_DST}"
install -D -m 0644 "${DESKTOP}" "${DESKTOP_DST}"
[[ -f "${ICON}" ]] && install -D -m 0644 "${ICON}" "${ICON_DST}"

refresh_desktop_db "${SHARE}/applications"

echo "==> Installed:"
echo "    ${BIN_DST}"
echo "    ${DESKTOP_DST}"
[[ -f "${ICON}" ]] && echo "    ${ICON_DST}"

# Warn if the chosen bin dir is not on PATH (common for ~/.local/bin).
case ":${PATH}:" in
    *":${PREFIX}/bin:"*) ;;
    *) echo
       echo "NOTE: ${PREFIX}/bin is not on your PATH. Add it, e.g.:"
       echo "      echo 'export PATH=\"${PREFIX}/bin:\$PATH\"' >> ~/.bashrc" ;;
esac

echo "==> Done. Run: png2obj --help"
