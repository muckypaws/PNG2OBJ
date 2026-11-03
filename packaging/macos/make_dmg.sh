#!/usr/bin/env bash
# =============================================================================
# packaging/macos/make_dmg.sh
# -----------------------------------------------------------------------------
# Package dist/PNG2OBJ.app (produced by packaging/build_macos.sh) into a
# drag-to-Applications .dmg.
#
# Output: dist/PNG2OBJ-<version>.dmg
#
# Uses `create-dmg` (https://github.com/create-dmg/create-dmg) when available
# for a nice window layout with an /Applications symlink; otherwise falls back
# to plain `hdiutil`.
#
# NOTE: macOS-only (hdiutil/create-dmg are macOS tools). Authored for native
# macOS / the macos-latest CI runner; not executed on Linux.
#
# Usage:
#   packaging/build_macos.sh          # produce dist/PNG2OBJ.app first
#   packaging/macos/make_dmg.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist"
APP="${DIST_DIR}/PNG2OBJ.app"
VERSION="3.0.0"
VOLNAME="PNG2OBJ ${VERSION}"
OUTPUT="${DIST_DIR}/PNG2OBJ-${VERSION}.dmg"
ICON="${REPO_ROOT}/packaging/assets/png2obj.icns"

cd "${REPO_ROOT}"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "WARNING: not macOS (uname=$(uname -s)); hdiutil/create-dmg unavailable here." >&2
fi
if [[ ! -d "${APP}" ]]; then
    echo "ERROR: ${APP} not found. Run packaging/build_macos.sh first." >&2
    exit 1
fi

mkdir -p "${DIST_DIR}"
rm -f "${OUTPUT}"

if command -v create-dmg >/dev/null 2>&1; then
    echo "==> Building DMG with create-dmg"
    CREATE_DMG_ARGS=(
        --volname "${VOLNAME}"
        --window-pos 200 120
        --window-size 640 400
        --icon-size 128
        --icon "PNG2OBJ.app" 160 200
        --app-drop-link 480 200
        --no-internet-enable
    )
    if [[ -f "${ICON}" ]]; then
        CREATE_DMG_ARGS+=(--volicon "${ICON}")
    fi
    # create-dmg returns non-zero if it only had warnings; guard accordingly.
    create-dmg "${CREATE_DMG_ARGS[@]}" "${OUTPUT}" "${APP}" || {
        if [[ ! -f "${OUTPUT}" ]]; then
            echo "ERROR: create-dmg failed and no DMG was produced." >&2
            exit 1
        fi
    }
else
    echo "==> create-dmg not found; falling back to hdiutil"
    STAGING="$(mktemp -d)"
    cp -R "${APP}" "${STAGING}/"
    ln -s /Applications "${STAGING}/Applications"
    hdiutil create \
        -volname "${VOLNAME}" \
        -srcfolder "${STAGING}" \
        -ov -format UDZO \
        "${OUTPUT}"
    rm -rf "${STAGING}"
fi

echo "==> Done: ${OUTPUT}"
ls -lh "${OUTPUT}"
echo
echo "    To codesign + notarize (requires your Apple Developer ID), see"
echo "    packaging/README.md 'Signing & notarization'."
