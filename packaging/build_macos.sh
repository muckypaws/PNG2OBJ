#!/usr/bin/env bash
# =============================================================================
# packaging/build_macos.sh
# -----------------------------------------------------------------------------
# Build a standalone macOS .app bundle of the PNG2OBJ CLI using Nuitka.
#
# Entry point : PNG2ObjV3.py  (argparse CLI that imports the png2obj package)
# Output      : dist/PNG2OBJ.app  (a standalone application bundle)
#
# NOTE: Nuitka cannot cross-compile. This script is authored to run on a native
# macOS host (locally or on a `macos-latest` GitHub Actions runner). It has NOT
# been executed on Linux; it is parse-checked only in this environment.
#
# Usage:
#   packaging/build_macos.sh
#
# Prerequisites (see packaging/README.md):
#   - macOS with Xcode command line tools (clang)
#   - Python 3.11+ (python.org or Homebrew build, universal2 if you want a
#     universal binary)
#   - pip install -r requirements.txt -r requirements-build.txt
#
# Shared Nuitka flags live in packaging/nuitka_common.txt (single source of
# truth). GUI (PySide6/VTK) flags are added there, not here.
# =============================================================================
set -euo pipefail

# --- Resolve paths ----------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMMON_FLAGS_FILE="${SCRIPT_DIR}/nuitka_common.txt"

ENTRY_POINT="${REPO_ROOT}/PNG2ObjV3.py"
BUILD_DIR="${REPO_ROOT}/build/macos"
DIST_DIR="${REPO_ROOT}/dist"
APP_NAME="PNG2OBJ"
ICON_FILE="${SCRIPT_DIR}/assets/png2obj.icns"   # optional; used only if present

PYTHON="${PYTHON:-python3}"

cd "${REPO_ROOT}"

echo "==> PNG2OBJ macOS build"
echo "    repo root : ${REPO_ROOT}"
echo "    entry     : ${ENTRY_POINT}"
echo "    python    : $(${PYTHON} --version 2>&1)"

# --- Sanity checks ----------------------------------------------------------
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "WARNING: not running on macOS (uname=$(uname -s))." >&2
    echo "         Nuitka cannot cross-compile a macOS .app from this host." >&2
    echo "         Run this on a macOS machine or the macos-latest CI runner." >&2
fi
if [[ ! -f "${ENTRY_POINT}" ]]; then
    echo "ERROR: entry point not found: ${ENTRY_POINT}" >&2
    exit 1
fi
if [[ ! -f "${COMMON_FLAGS_FILE}" ]]; then
    echo "ERROR: shared flags file not found: ${COMMON_FLAGS_FILE}" >&2
    exit 1
fi
if ! "${PYTHON}" -c "import nuitka" 2>/dev/null; then
    echo "ERROR: Nuitka is not installed for ${PYTHON}." >&2
    echo "       Run: ${PYTHON} -m pip install -r requirements.txt -r requirements-build.txt" >&2
    exit 1
fi

# --- Load shared flags into an array ---------------------------------------
COMMON_FLAGS=()
while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    [[ "${line}" =~ ^[[:space:]]*# ]] && continue
    COMMON_FLAGS+=("${line}")
done < "${COMMON_FLAGS_FILE}"

# --- macOS-specific flags ---------------------------------------------------
MACOS_FLAGS=(
    # Produce PNG2OBJ.app rather than a bare executable tree.
    --macos-create-app-bundle
    "--macos-app-name=${APP_NAME}"
    "--macos-app-version=3.0.0"
    "--output-dir=${BUILD_DIR}"
    # ---------------------------------------------------------------------
    # FUTURE GUI EXTENSION POINT (macOS):
    #   A CLI tool is a "background" app. When the GUI arrives, drop the
    #   background mode so it gets a Dock icon and menu bar:
    #       (remove) --macos-app-mode=background
    #   and enable PySide6/VTK in packaging/nuitka_common.txt.
    # ---------------------------------------------------------------------
    --macos-app-mode=background
)

# Target architecture. Default: build for the host arch (works with any
# CPython). Set MACOS_ARCH=universal for a universal2 binary — this REQUIRES a
# universal2 CPython (e.g. the python.org installer); the arch-specific builds
# from actions/setup-python cannot produce it.
if [[ -n "${MACOS_ARCH:-}" ]]; then
    MACOS_FLAGS+=("--macos-target-arch=${MACOS_ARCH}")
fi

# Attach an icon only if one has been added to packaging/assets/.
if [[ -f "${ICON_FILE}" ]]; then
    MACOS_FLAGS+=("--macos-app-icon=${ICON_FILE}")
else
    echo "    (no icon at ${ICON_FILE}; building without a custom app icon)"
fi

mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

echo "==> Running Nuitka (standalone + .app bundle)..."
set -x
"${PYTHON}" -m nuitka \
    "${COMMON_FLAGS[@]}" \
    "${MACOS_FLAGS[@]}" \
    "${ENTRY_POINT}"
set +x

# --- Collect artifact -------------------------------------------------------
# Nuitka names the bundle after the entry module (PNG2ObjV3.app); normalise to
# PNG2OBJ.app in dist/.
PRODUCED_APP="$(find "${BUILD_DIR}" -maxdepth 1 -type d -name '*.app' | head -n1 || true)"
if [[ -z "${PRODUCED_APP}" ]]; then
    echo "ERROR: no .app bundle produced in ${BUILD_DIR}" >&2
    exit 1
fi

rm -rf "${DIST_DIR}/${APP_NAME}.app"
cp -R "${PRODUCED_APP}" "${DIST_DIR}/${APP_NAME}.app"

echo "==> Done."
echo "    App bundle: ${DIST_DIR}/${APP_NAME}.app"
echo
echo "    Next steps:"
echo "      - Package into a .dmg:  packaging/macos/make_dmg.sh"
echo "      - Codesign + notarize (requires your Apple Developer ID): see"
echo "        packaging/README.md 'Signing & notarization'."
