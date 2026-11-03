#!/usr/bin/env bash
# =============================================================================
# packaging/build_linux.sh
# -----------------------------------------------------------------------------
# Build a standalone, single-file Linux executable of the PNG2OBJ CLI using
# Nuitka.
#
# Entry point : PNG2ObjV3.py  (argparse CLI that imports the png2obj package)
# Output      : dist/png2obj  (one self-contained ELF executable)
#
# Usage:
#   packaging/build_linux.sh
#
# Prerequisites (see packaging/README.md):
#   - Python 3.11+
#   - A C compiler (gcc or clang) and patchelf
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
BUILD_DIR="${REPO_ROOT}/build/linux"
DIST_DIR="${REPO_ROOT}/dist"
OUTPUT_NAME="png2obj"

PYTHON="${PYTHON:-python3}"

cd "${REPO_ROOT}"

echo "==> PNG2OBJ Linux build"
echo "    repo root : ${REPO_ROOT}"
echo "    entry     : ${ENTRY_POINT}"
echo "    python    : $(${PYTHON} --version 2>&1)"

# --- Sanity checks ----------------------------------------------------------
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
# Strip comments (# ...) and blank lines; keep each remaining line as one arg.
COMMON_FLAGS=()
while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    [[ "${line}" =~ ^[[:space:]]*# ]] && continue
    COMMON_FLAGS+=("${line}")
done < "${COMMON_FLAGS_FILE}"

# --- Linux-specific flags ---------------------------------------------------
LINUX_FLAGS=(
    # One self-contained executable (the standalone folder is packed inside).
    --onefile
    # Name of the produced binary -> dist/png2obj
    "--output-filename=${OUTPUT_NAME}"
    "--output-dir=${BUILD_DIR}"
    # Keep onefile unpacking deterministic/per-version under the user cache.
    "--onefile-tempdir-spec={CACHE_DIR}/png2obj/{VERSION}"
    # ---------------------------------------------------------------------
    # FUTURE GUI EXTENSION POINT (Linux):
    #   No extra Linux-only flags are needed for PySide6/VTK — enabling the
    #   plugin in packaging/nuitka_common.txt is sufficient. If the GUI needs
    #   an application icon embedded, add e.g.:
    #       --linux-icon=packaging/assets/png2obj.png
    # ---------------------------------------------------------------------
)

mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

echo "==> Running Nuitka (standalone + onefile)..."
set -x
"${PYTHON}" -m nuitka \
    "${COMMON_FLAGS[@]}" \
    "${LINUX_FLAGS[@]}" \
    "${ENTRY_POINT}"
set +x

# --- Collect artifact -------------------------------------------------------
PRODUCED="${BUILD_DIR}/${OUTPUT_NAME}"
if [[ ! -f "${PRODUCED}" ]]; then
    # Nuitka onefile may append .bin on some setups; fall back to a glob.
    PRODUCED="$(find "${BUILD_DIR}" -maxdepth 1 -type f -name "${OUTPUT_NAME}*" ! -name '*.o' | head -n1 || true)"
fi
if [[ -z "${PRODUCED}" || ! -f "${PRODUCED}" ]]; then
    echo "ERROR: expected output executable not found in ${BUILD_DIR}" >&2
    exit 1
fi

cp -f "${PRODUCED}" "${DIST_DIR}/${OUTPUT_NAME}"
chmod +x "${DIST_DIR}/${OUTPUT_NAME}"

echo "==> Done."
echo "    Executable: ${DIST_DIR}/${OUTPUT_NAME}"
ls -lh "${DIST_DIR}/${OUTPUT_NAME}"
