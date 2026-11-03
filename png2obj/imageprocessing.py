"""Loaded-image state.

Holds the decoded PNG and the derived bounding box of visible pixels, replacing
the former loose module globals (pattern, pattern_w/h, pattern_meta, channels,
Image_Min/Max X/Y, Image_Real_Width/Height). A single instance is created and
populated at load time; defaults match the original pre-load global values (0).
"""

import os
import sys
import png
from pathlib import Path

class LoadedImage:
    """Decoded PNG pixel grid plus the visible-pixel bounding box.

    Attributes:
        pattern: row-major pixel data as returned by pypng (list of rows).
        width (int): PNG width in pixels (was pattern_w).
        height (int): PNG height in pixels (was pattern_h).
        meta (dict): pypng metadata (was pattern_meta).
        channels (int): channels per pixel, 3 (RGB) or 4 (RGBA).
        min_x, max_x, min_y, max_y (int): bounding box of non-transparent pixels.
        real_width, real_height (int): size of that bounding box.
    """

    def __init__(self):
        self.pattern = 0
        self.width = 0
        self.height = 0
        self.meta = 0
        self.channels = 0
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0
        self.real_width = 0
        self.real_height = 0

# runtime imported after the class so the package stays cycle-safe.
from png2obj import runtime


#
# Convert Colour To Pixel - Can extend this to exclude colour ranges in future updates.
#
def getPixelFromRow(x, row, channels, rowWidth):
    """
    Extract a pixel's RGB(A) data from a given row of image data and determine material index.

    This function interprets raw pixel data (indexed or RGB/RGBA), evaluates transparency,
    and registers a colour as a material if valid. It returns the pixel intensity,
    the assigned material index, and the hex colour code.

    Args:
        x (int): Horizontal pixel index within the row.
        row (list[int]): Flattened image row data (byte list).
        channels (int): Number of channels per pixel (1=Indexed, 3=RGB, 4=RGBA).
        rowWidth (int): Total number of pixels in the row.

    Returns:
        tuple:
            - int: Pixel value (0-255) or -1 for transparent/invalid
            - int: Index of material in material dictionary, or -1 if invalid
            - str: Hex colour code (e.g. "#ffcc00") or default "#000000"

    Globals:
        ALPHACUTOFF (int): Threshold below which alpha is considered transparent.
        MATERIALS.colours (dict): Maps colour hex codes to usage count.
        MATERIALS.index (int): Material creation tracker.
        Create_Towered_File (bool): Affects towered output behaviour.

    TODO:
        - Refactor RGB/Alpha logic into a reusable pixel parser
        - Expose ALPHACUTOFF and Create_Towered_File as arguments or config
        - Add support for 16-bit PNGs or grayscale+alpha channels
    """
    # Calculate the offset into the ROW for pixel information
    offset_x = (x * channels) % (rowWidth * channels)
    pixel = 0
    ColourCode = "#000000"

    # Need the current Index of Colour or do we? Could use dict len?

    TowerMultiplier = 1.0

    # Alpha for this pixel, where the image carries one. ``None`` means fully
    # opaque (no alpha channel / palette transparency), so the cutoff below is
    # skipped entirely and RGB / RGBA behaviour is preserved exactly.
    a = None

    if channels == 1:
        # Single value per pixel: either a palette index or a grey level.
        meta = runtime.IMAGE.meta
        palette = meta.get('palette') if isinstance(meta, dict) else None
        if palette:
            # Indexed / palette PNG: look the RGB(A) colour up by index.
            entry = palette[row[x]]
            r, g, b = entry[0], entry[1], entry[2]
            if len(entry) > 3:
                a = entry[3]
        else:
            # Greyscale PNG: one intensity maps to r == g == b.
            r = g = b = row[x]
        pixel = r | g | b

    elif channels == 2:
        # Greyscale + alpha: [grey, alpha] per pixel.
        r = g = b = row[offset_x]
        a = row[offset_x + 1]
        pixel = r | g | b

    else:
        # Get the RGB Values from the offset
        r, g, b = row[offset_x:offset_x + 3]

        # Crude but effective as we're only interested in whether colour data
        # is prsent or not to determine whether to add a primitive or not
        pixel = r|g|b

        if channels == 4:
            # Check Alpha
            a = row[offset_x + 3]

    # If an alpha value is present and below the cutoff we treat the pixel as
    # having no colour data (transparent). Applied uniformly for RGBA,
    # greyscale+alpha and palette transparency.
    if a is not None and a <= runtime.ALPHACUTOFF:
        pixel = -1
        r = 0
        g = 0
        b = 0

    valid, ColourCode = runtime.MATERIALS.register(r, g, b, pixel)

    if not valid:
        pixel =-1


    material_index = -1
    
    # Retrieve the index of the Colour Code from the Dictionary
    if ColourCode in runtime.MATERIALS.colours and pixel > -1:
        material_index = list(runtime.MATERIALS.colours).index(ColourCode)
        runtime.MATERIALS.colours[ColourCode] += 1

    return pixel, material_index, ColourCode



#
# Process a simple set of rules to determine if a Jointer Block is required.
# That is missing diagonal pixes.  It's crude and needs refinement.
#
def CheckJointRequired(x ,y ,row, nextRow, channels, pattern_w):
    """
    Check if a pixel joint is needed to strengthen corner-only diagonal connections in the print.

    This is used to detect weak diagonals where two pixels only touch at the corner,
    with adjacent spaces in between. Such configurations (e.g. XO/OX or OX/XO)
    result in fragile prints, especially on flat or thin-layered models.

    The function inspects a 2x2 pixel area and identifies situations where a
    small strengthening joint should be added between opposing corners.

    Args:
        x (int): Pixel's X-coordinate in the current row.
        y (int): Pixel's Y-coordinate in the image.
        row (list[int]): Flattened list of pixel data for the current row.
        nextRow (list[int]): Flattened list of pixel data for the next row.
        channels (int): Number of channels in the image data (e.g. 3 = RGB).
        pattern_w (int): Width of the pixel row.

    Returns:
        int:
            - 0 = No joint needed
            - 1 = Add joint (↘ diagonal from top-left to bottom-right)
            - -1 = Add joint (↙ diagonal from top-right to bottom-left)

    Globals:
        Pixel_W (int): Width of a sprite frame (used to avoid placing joints at sprite edges).
        Pixel_H (int): Height of a sprite frame.

    Note:
        This logic is used regardless of print mode (flat, layered, or towered) to ensure print
        strength and prevent brittle isolated pixels with corner-only contact.

    TODO:
        - Make `Pixel_W` and `Pixel_H` configurable or passed in
        - Consider returning a label/enum for joint type instead of int
        - Add optional debug visual output to preview joints pre-print
    """
    isJointRequired = 0

    # Check if we've Reached the boundary of the Sprite Sheet Sprite
    if y > 0 and not (y+1) % runtime.Pixel_H:
        return 0
    
    if x>0 and not (x+1) % runtime.Pixel_W:
        return 0

    # Not Checking last pixel as this is covered 
    if x >= (pattern_w-1): 
        return isJointRequired

    a, mi, mm = getPixelFromRow(x,   row,     channels, pattern_w)
    b, mi, mm = getPixelFromRow(x+1, row,     channels, pattern_w)
    c, mi, mm = getPixelFromRow(x,   nextRow, channels, pattern_w)
    d, mi, mm = getPixelFromRow(x+1, nextRow, channels, pattern_w)

    if (a > 0 and d > 0 and b <= 0 and c <= 0):
        isJointRequired = 1

    if (b > 0 and c > 0 and a <= 0 and d <= 0):
        isJointRequired = -1

    return isJointRequired




#
# Load a PNG File
#
def load_pattern(pattern_name):
    """
    Load a pre-saved PNG pattern file from the local pattern directory.

    This is used for frame overlays, template elements, or repeatable embedded
    components. The function attempts to read the file, parse its PNG metadata,
    and convert the result to a usable list.

    Args:
        pattern_name (str): Name of the pattern PNG file (without extension).

    Returns:
        tuple:
            - pattern (list): Raw pixel data from PNG
            - pattern_w (int): Width of the pattern
            - pattern_h (int): Height of the pattern
            - pattern_meta (dict): PNG metadata (e.g. bit depth, channels)

    Globals:
        PATTERNS (str): Path to the folder where pattern PNGs are stored.

    TODO:
        - Add error handling for non-PNG file types
        - Allow extension override or auto-detect
        - Cache last-read pattern for re-use
    """
    pattern_file = os.path.join(runtime.PATTERNS, "{}.png".format(Path(pattern_name).with_suffix('')))

    runtime.log(f"Attempting to pre-process file: {pattern_file}")
    if not os.path.isfile(pattern_file):
        runtime.log("Invalid PNG file: {}".format(pattern_file))
        return None, 0, 0, None

    # Scope B/D: read the PNG defensively. The file handle is managed by a
    # context manager (closed even on error), the header is validated and the
    # dimensions are size-checked BEFORE the decoded rows are allocated, and
    # any decode failure (corrupt / truncated / non-PNG data) is reported as a
    # clean message with a non-zero exit instead of a raw traceback.
    try:
        with open(pattern_file, 'rb') as fp_png:
            reader = png.Reader(file=fp_png)
            pattern_w, pattern_h, rows, pattern_meta = reader.read()

            # Guard against dimension / decompression bombs before we
            # materialise (and therefore allocate) the full pixel grid.
            _check_image_size(pattern_file, pattern_w, pattern_h)

            # Materialise the lazy row iterator while the file is still open.
            # Matches the original `list(...)` behaviour exactly.
            pattern = list(rows)
    except SystemExit:
        # _check_image_size / a nested guard already reported and is exiting.
        raise
    except Exception as error:
        runtime.log(
            f"Error: '{pattern_file}' could not be read as a valid PNG "
            f"({type(error).__name__}: {error})"
        )
        sys.exit(1)

    runtime.log("Loaded PNG file: {}".format(pattern_file))
    return pattern, pattern_w, pattern_h, pattern_meta


def _check_image_size(pattern_file, width, height):
    """Reject oversized PNGs before their pixel data is allocated.

    Enforces the ``runtime.MAX_IMAGE_DIMENSION`` per-axis cap and the
    ``runtime.MAX_IMAGE_PIXELS`` total-pixel cap as a defence against crafted
    dimension / decompression-bomb images. On violation it logs a clear
    message and exits non-zero (sys.exit(1)); normal images pass untouched.
    """
    if width <= 0 or height <= 0:
        runtime.log(
            f"Error: '{pattern_file}' has invalid dimensions "
            f"({width}x{height})"
        )
        sys.exit(1)

    if width > runtime.MAX_IMAGE_DIMENSION or height > runtime.MAX_IMAGE_DIMENSION:
        runtime.log(
            f"Error: '{pattern_file}' dimensions {width}x{height} exceed the "
            f"maximum allowed dimension of {runtime.MAX_IMAGE_DIMENSION}px per "
            f"side; refusing to load."
        )
        sys.exit(1)

    if width * height > runtime.MAX_IMAGE_PIXELS:
        runtime.log(
            f"Error: '{pattern_file}' has {width * height} pixels "
            f"({width}x{height}), exceeding the maximum of "
            f"{runtime.MAX_IMAGE_PIXELS}; refusing to load."
        )
        sys.exit(1)



#
# Load PNG File to Memory and perform some initial processing
#   Check number of Channels, is Alpha Available, discover all colours in image
#
def loadPNGToMemory(Filename):
    """
    Load a PNG file from disk into memory and validate its structure.

    This function reads the image file, checks the bit depth, detects alpha channel presence,
    and assigns global pattern data required for further processing. It also triggers
    discovery of colour layers used for slicing or object generation.

    Args:
        Filename (str): Path to the PNG file to load.

    Returns:
        bool: True if file loaded and passed basic checks; False if unsupported or missing.

    Globals:
        pattern (list[list[int]]): Raw pixel data grid.
        pattern_w (int): Width in pixels.
        pattern_h (int): Height in pixels.
        pattern_meta (dict): Metadata including planes and alpha presence.
        channels (int): Number of channels (3 = RGB, 4 = RGBA).

    TODO:
        - Refactor to return pattern metadata instead of using globals
        - Consider supporting more colour modes or bit depths
        - Expand error reporting to include file format and image mode issues
    """
    # Load the PNG File, Check if Valid

    runtime.IMAGE.pattern, runtime.IMAGE.width, runtime.IMAGE.height, runtime.IMAGE.meta = load_pattern(Filename)

    # If File Wasn't Found Time to Quit
    if runtime.IMAGE.pattern is None:
        return False

    # Determine the number of values per pixel in the decoded rows. For RGB /
    # RGBA the historical behaviour is preserved exactly (3, or 4 when an alpha
    # channel is present). Greyscale (1 plane), greyscale+alpha (2 planes) and
    # palette/indexed PNGs (1 plane, with a palette) are now also supported;
    # getPixelFromRow converts each to RGB(A) so the rest of the pipeline is
    # unchanged.
    planes = runtime.IMAGE.meta['planes']
    alpha = runtime.IMAGE.meta['alpha']

    if planes >= 3:
        runtime.IMAGE.channels = 4 if alpha else 3
    else:
        # 1 = greyscale or palette/indexed, 2 = greyscale + alpha.
        runtime.IMAGE.channels = planes

    discoverPixelLayers()

    return True



# Work out the number of colours in the PNG
# Also the True Width/Height taking out Pixels with Alpha Channels
def discoverPixelLayers():
    """
    Analyse the loaded PNG pattern to find the bounding box of active pixels.

    This function calculates the minimum and maximum X/Y coordinates of all visible
    pixels (i.e., those above the alpha cutoff) and stores them in global variables.
    These bounds define the real sprite dimensions used for layout and scaling.

    Returns:
        None. Updates global image metrics in-place.

    Globals:
        pattern (list[list[int]]): Loaded image data.
        pattern_w (int): Width of the loaded PNG.
        pattern_h (int): Height of the loaded PNG.
        channels (int): Number of channels per pixel.
        Image_MinX (int): Minimum X of visible area.
        Image_MaxX (int): Maximum X of visible area.
        Image_MinY (int): Minimum Y of visible area.
        Image_MaxY (int): Maximum Y of visible area.
        Image_Real_Width (int): Width of bounding box.
        Image_Real_Height (int): Height of bounding box.

    TODO:
        - Support trimming transparent borders automatically
        - Move pixel logic to a re-usable pixel scanner
        - Consider returning a bounding box object
    """
    # Work our way through each row of the PNG File.
    global Image_Total_Colours

    minx = 999999999
    maxx = 0
    miny = 999999999
    maxy = 0 
    for y in range(runtime.IMAGE.height):
        row = runtime.IMAGE.pattern[int(y % runtime.IMAGE.height)]

        for x in range(runtime.IMAGE.width):
            # Get Pixel from Row
            pixel = getPixelFromRow(x, row, runtime.IMAGE.channels, runtime.IMAGE.width)[0]

            # Pixel set to -1 for Transperent Pixel (Based on ALPHA Cutoff)
            if pixel >= 0:
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                if y < miny:
                    miny = y
                if y > maxy:
                    maxy = y

    runtime.IMAGE.min_x = minx
    runtime.IMAGE.max_x = maxx
    runtime.IMAGE.min_y = miny
    runtime.IMAGE.max_y = maxy
    runtime.IMAGE.real_width = maxx - minx + 1
    runtime.IMAGE.real_height = maxy - miny + 1
