#!/usr/bin/env bash
# =============================================================================
# packaging/linux/make_appimage.sh
# -----------------------------------------------------------------------------
# Turn the standalone Linux build (dist/png2obj, produced by
# packaging/build_linux.sh) into a portable AppImage.
#
# Output: dist/PNG2OBJ-<arch>.AppImage
#
# Strategy:
#   1. Assemble an AppDir (AppRun + .desktop + icon + the binary).
#   2. Run appimagetool to pack it.
#
# FUSE note: appimagetool is itself an AppImage and normally needs FUSE. In
# sandboxes/CI without FUSE we fall back to APPIMAGE_EXTRACT_AND_RUN=1, which
# extracts and runs it without the kernel module. If packing still cannot run,
# the assembled AppDir is left in place and documented as the deliverable.
#
# Usage:
#   packaging/build_linux.sh            # produce dist/png2obj first
#   packaging/linux/make_appimage.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist"
BINARY="${DIST_DIR}/png2obj"
ICON="${REPO_ROOT}/packaging/assets/png2obj.png"
DESKTOP="${SCRIPT_DIR}/PNG2OBJ.desktop"

ARCH="$(uname -m)"
APPDIR="${REPO_ROOT}/build/linux/AppDir"
OUTPUT="${DIST_DIR}/PNG2OBJ-${ARCH}.AppImage"

cd "${REPO_ROOT}"

echo "==> PNG2OBJ AppImage build (arch=${ARCH})"

# --- Checks -----------------------------------------------------------------
if [[ ! -f "${BINARY}" ]]; then
    echo "ERROR: ${BINARY} not found. Run packaging/build_linux.sh first." >&2
    exit 1
fi

# --- Assemble AppDir --------------------------------------------------------
echo "==> Assembling AppDir at ${APPDIR}"
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin" \
         "${APPDIR}/usr/share/applications" \
         "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

cp "${BINARY}" "${APPDIR}/usr/bin/png2obj"
chmod +x "${APPDIR}/usr/bin/png2obj"

# Desktop file (required at AppDir root by appimagetool).
cp "${DESKTOP}" "${APPDIR}/png2obj.desktop"
cp "${DESKTOP}" "${APPDIR}/usr/share/applications/png2obj.desktop"

# Icon (required at AppDir root, named to match the .desktop Icon= key).
if [[ -f "${ICON}" ]]; then
    cp "${ICON}" "${APPDIR}/png2obj.png"
    cp "${ICON}" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/png2obj.png"
else
    echo "WARNING: icon ${ICON} missing; AppImage will have no icon." >&2
fi

# AppRun launcher: forward all arguments to the bundled binary.
cat > "${APPDIR}/AppRun" <<'APPRUN'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/png2obj" "$@"
APPRUN
chmod +x "${APPDIR}/AppRun"

# --- Obtain appimagetool ----------------------------------------------------
TOOL=""
if command -v appimagetool >/dev/null 2>&1; then
    TOOL="appimagetool"
else
    TOOL_PATH="${REPO_ROOT}/build/linux/appimagetool-${ARCH}.AppImage"
    if [[ ! -f "${TOOL_PATH}" ]]; then
        echo "==> Downloading appimagetool..."
        URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
        if ! curl -fsSL "${URL}" -o "${TOOL_PATH}"; then
            echo "ERROR: could not download appimagetool from ${URL}" >&2
            echo "       AppDir is assembled at ${APPDIR}; pack it on a host with appimagetool." >&2
            exit 1
        fi
        chmod +x "${TOOL_PATH}"
    fi
    TOOL="${TOOL_PATH}"
fi

# --- Pack -------------------------------------------------------------------
echo "==> Packing AppImage -> ${OUTPUT}"
mkdir -p "${DIST_DIR}"

# Prefer a normal (FUSE) run; fall back to extract-and-run where FUSE is
# unavailable (common in containers/CI). ARCH export is required by newer
# appimagetool releases.
run_tool() {
    ARCH="${ARCH}" "${TOOL}" "$@"
}
run_tool_no_fuse() {
    APPIMAGE_EXTRACT_AND_RUN=1 ARCH="${ARCH}" "${TOOL}" "$@"
}

if run_tool "${APPDIR}" "${OUTPUT}" 2> >(tee /tmp/appimage_err >&2); then
    :
elif grep -qiE 'fuse|dlopen|libfuse' /tmp/appimage_err 2>/dev/null; then
    echo "==> FUSE unavailable; retrying with APPIMAGE_EXTRACT_AND_RUN=1"
    run_tool_no_fuse "${APPDIR}" "${OUTPUT}"
else
    echo "ERROR: appimagetool failed (see output above)." >&2
    echo "       AppDir remains at ${APPDIR} and can be packed on another host." >&2
    exit 1
fi

if [[ -f "${OUTPUT}" ]]; then
    chmod +x "${OUTPUT}"
    echo "==> Done: ${OUTPUT}"
    ls -lh "${OUTPUT}"
else
    echo "ERROR: AppImage not produced." >&2
    exit 1
fi
