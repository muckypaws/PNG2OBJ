"""Shared runtime state for PNG2ObjV3.

Single home for the cross-cutting state the converter threads through its
functions: the three domain objects (image, material registry, SVG builder),
the run-wide configuration / tuning values, and the logger. Modules reference
these as ``runtime.<name>`` so that reads and writes are shared across the
package without passing everything by argument.

Import as ``from png2obj import runtime`` (a module binding) and access
attributes at call time; do not ``from png2obj.runtime import IMAGE`` at import
time, so the package stays safe against import cycles.
"""
import sys
from datetime import datetime

from png2obj.imageprocessing import LoadedImage
from png2obj.materials import MaterialRegistry
from png2obj.svg import SvgState

# --- Domain state objects (one instance per run) ---
IMAGE = LoadedImage()
MATERIALS = MaterialRegistry()
SVG = SvgState()

# --- Application defaults / tuning ---
DEBUG = False

# Default directory for input/pattern files ("" == current directory).
PATTERNS = ""

# Sentinel "no fixed sprite size" value for sprite-sheet slicing.
DEFAULT_PIXEL_WIDTH = 99999999
DEFAULT_PIXEL_HEIGHT = 99999999

# Fixed sprite width/height within a sprite sheet (sentinel == whole image).
Pixel_W = DEFAULT_PIXEL_WIDTH
Pixel_H = DEFAULT_PIXEL_HEIGHT

# Primitive cube size. X positive, Y negative (original axis convention).
CUBE_X = 10
CUBE_Y = -10

# Alpha threshold: pixels with alpha <= this are treated as transparent.
ALPHACUTOFF = 128

# --- PNG decompression-bomb guards ---
# Reject images whose total pixel count (width*height) exceeds this cap, and
# any image whose single dimension exceeds MAX_IMAGE_DIMENSION, before the
# decoded rows are allocated or scanned. The defaults are generous: every
# bundled test image is orders of magnitude smaller, so normal use is
# unaffected. These exist to stop a crafted/corrupt PNG from exhausting memory.
MAX_IMAGE_PIXELS = 100_000_000      # 100 megapixels (e.g. 10000 x 10000)
MAX_IMAGE_DIMENSION = 100_000       # cap on width or height individually

# Add jointer cubes between corner-only diagonal pixels (for printing).
JOINTS_REQUIRED = False

# Emit a corresponding .MTL material file for coloured cubes.
CREATE_MTL_FILE = False

# Base output filename (no extension).
WORKING_FILENAME = ""

# Output file counter (distinguishes layered outputs).
FILE_COUNTER = 0

# Material (.mtl) output paths.
mtl_filename = ""
mtl_lib_filename = ""

# Running face/normal index counters for OBJ vertex referencing.
Current_Face = 0
Current_Opposite_Face = 0

# Accumulating Z offset applied as layers are stacked.
CurrentZOffset = 0.0

# Z-depth multipliers.
Primitive_Multiplier_Background = 1.0
Primitive_Multiplier_Layers = 1.0

# Treat all colour layers as the same height (grouped, separate files).
ColoursOnSingleLayerHeight = False

# Colour sorting for layer order.
Sort_Colours_Flag = False
Sort_Direction = False  # False = low->high, True = high->low

# Output-mode flags.
Create_Layered_File = False
Create_Towered_File = False

# Last coloured pixel found (layer-processing state).
lastPixelFound = 0

# Emit the ASCII debug .txt file.
Debug_Txt_File = False

# Object X/Y scale multiplier (pixel -> mm).
Primitive_Multipler = 0.1

# Per-layer Z depth, and an optional distinct first-layer depth.
Primitive_Layer_Depth = 0.0
Primitive_Initial_Layer_Depth = 0.0


def log(msg):
    """Print a timestamped message to stdout, flushed immediately.

    Args:
        msg (str): The message to log.
    """
    sys.stdout.write(str(datetime.now()))
    sys.stdout.write(": ")
    sys.stdout.write(msg)
    sys.stdout.write("\n")
    sys.stdout.flush()
