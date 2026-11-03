#!/usr/bin/env python3
"""PNG2ObjV3: Convert pixel PNGs into 3D OBJ or SVG files with optional layering and illusion support."""
# PNG2ObjV3
# Version: 3.0.0
# Author: Jason Brooks (muckypaws)
# License: MIT with additional non-commercial use restriction
# https://github.com/muckypaws/PNG2OBJ
#
# Created by Jason Brooks: www.muckypaws.com and www.wonkypix.com
#            3rd June 2022
#
# This simple code takes a PNG File and converts any colour pixel found to a primitive
# It will search along the X-Axis to combine primitives from a cube to a box where appropriate
# If you have fixed width sprites in a sheet, then use the Pixel_W and Pixel_H to set the bounding widths
# This will force a gap between sprites
# There's much that can be done to optimise the code
#
# V1.00 - 3rd June 2022      - The Platty Joobs Edition ;)
# V1.01 - 5th June 2022      - The Platty Pudding Edition ;)
#                              Add Jointer Cubes for diagonal pixels without support
#                              Only needed if you're using a printer.
# V1.02 - 28th June 2022     - Over the Rainbow Edition
#                              Added Option to Add Material File for Coloured Pixels
# V1.03 - 4th September 2023 - Welcome to the Layer Cake Edition
#                              Added Processing for Multiple Layers
#                              Added Option to Size Model in mm (-mw or -mh Maximum Width, Maximum Height)
# V1.04 - 23rd August 2024   - The Matrix Edition
#                              Creating options to create Parametric Designs based on grid patterns
#                              Let's see where this goes...
# V1.05 - 2nd September 2024 - Use Your Illusion 1 Edition...
#                              Create SVG Files from PNG Image Information
#                              Yeah I know the codes a bit of mess right now, I need to seperate stuff
#                              into classes and optimise code.  But ... You know...
#                              Sure you can bitch about it, or... you could contribute and help improve
#                              this project... #JustSayin...
#
# Usage :-
#   PNG2OBJ.py Filename
#
#   i.e. ./PNG2OBJ SpriteSheet
#
#   If you don't include the file extension, will add the .PNG to the filename.
#
#   Two output files are created
#
#       Filename.obj    <-- Contains the WaveFront OBJ 3D Vertices information
#       Filename.txt    <-- Used for debugging, showing an ASCII representation
#                           Of what pixels were processed.
#       Filename.mtl    <-- Contains the Wavefront Material File information.

import argparse                         # 'bout time I added Parsing...
import os
import sys
import math
import png
import random
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# --- Phase 1: geometry tables and pure SVG primitives now live in png2obj ---
from png2obj.geometry import (
    cube_vertices, cube_normals, cube_faces,
    joint_verticies, joint_normals, joint_faces,
    default_mtl_params, update_vert,
)
from png2obj.svg_primitives import (
    create_array, plot_circle_points, draw_circle, print_array,
    add_svg_centeredText, add_svg_centeredCircle, add_svg_rectangle,
)

# Application Defaults
from png2obj import runtime
from png2obj.imageprocessing import (
    getPixelFromRow, CheckJointRequired, load_pattern,
    loadPNGToMemory, discoverPixelLayers,
)
# Default location for File


# Set Pixel Width and Height if Sprites are fixed width within the sheet, otherwise 
# use a high number.

# PNG Data for Image loaded
# --- Phase 2b: PNG + bounding-box state now lives in png2obj.imageprocessing ---


# X is positive, Y is negative unless you want to flip the image.
# Leave these alone, my initial mistake carried over... represents the value of the
# Primitive Cube defined as a 10 x 10 x 10... You can change it but... well...
# you really don't want to... trust me...
# unless you fix my code to handle this properly
# so yeah... leave it alone :)

# Define the Alpha Value as Cut Off For the Pixel

# Define TRUE if Printing, FALSE if anything else as not required

# Define TRUE if a corresponding MTL File is to be created for Colour Cubes

# Define the Working Filename

# define the File Counter

# Used to define the Current Face Counter
# Needed to ensure Vertices are correctly defined.

#
# The multiplier to use when creating the background object
#

#
# The multiplier to use when creating the background object
#


#
# When processing colours, only on height above background object
#

#
# Define the Colour Material Dictionary
#
# --- Phase 2a: material + colour-filter state now lives in png2obj.materials ---

#
# Colour Exclusion List
#

#
# Colour Process List
#
#
# Colours Require Sorting?
#

#
# Which type of Object File to Create?
#

#
# Direction to sort the colour list for processing
#   False = Low to High, True = High to Low...
#

#
# Last coloured Pixel Found
#

#
# Debug TXT File Required?
#

#
# Actual Pixels Found Details.
#
#
# Actual Image Found when removing Transparent Pixels
#

# Object X/Y Multiplier

# Object Z Multiplier for each layer

# If we need a specific Initial Layer, this will override.

# Create a Single Layered File with Object Heights Dependent on Colour Order
# provided in the Process Colour Order list

# Needed for SVG File Creation.
# --- Phase 2c: SVG constants + render state now live in png2obj.svg ---
from png2obj.svg import (
    SVG_HEADER, SVG_COLOUR_SETS,
    LIGHT_BLOCK_INDEX, DARK_BLOCK_INDEX, LIGHT_PIXEL_INDEX, DARK_PIXEL_INDEX,
)

# Contains SVG Data

# Illusion Array Data

# Canvas Width/Height



# Table is Defined as colours for Light Block, Dark Block, Light Pixel, Dark Pixel index 0, 1, 2, 3

# Some sample colour sets, feel free to amend/adjust as you desire

# Indexs into the colour table above.

# Create Circles instead of Diagonals?

# Custom ArgumentParser to make option flags case-insensitive
class CaseInsensitiveArgumentParser(argparse.ArgumentParser):
    """
    Override argparse.ArgumentParser to support case-insensitive option flags.

    This subclass normalises all option strings to lowercase before matching,
    allowing users to specify flags such as -SVG or --Layered without worrying
    about case sensitivity.

    Example:
        parser = CaseInsensitiveArgumentParser()
        parser.add_argument('--example')
        args = parser.parse_args(['--EXAMPLE', 'value'])  # Valid

    """

    def _get_option_tuples(self, option_string):
        # Normalize the option string to lowercase for case-insensitive matching
        option_string = option_string.lower()
        return super()._get_option_tuples(option_string)

def draw_diagonals_in_array(width :int, height: int):
    """
    Populate a global SVG.illusion_array with randomly staggered diagonal lines (*) for use in pixel-based optical illusions.

    The pattern is generated across a 2D square array, simulating visual streaks
    that create depth illusions when layered behind or around foreground objects.

    Args:
        width (int): Width of the array/grid in pixels.
        height (int): Height of the array/grid in pixels.

    Returns:
        None. Modifies global SVG.illusion_array in-place.
    """

    size = max(width, height)
    runtime.SVG.illusion_array = create_array(size)

    max_range = width + height + 1
    max_y = len(runtime.SVG.illusion_array)
    max_x = len(runtime.SVG.illusion_array[0])

    line_streak = none_line_streak = 0

    for x in range(max_range):
        start_y = max(0, x - width)
        range_x = min(x, width)

        # Determine if a diagonal line should be drawn
        rand = random.randint(0, 10)
        draw_line = False
        
        if rand > 5:
            line_streak, none_line_streak = line_streak + 1, 0
            draw_line = line_streak < 2
        else:
            none_line_streak, line_streak = none_line_streak + 1, 0
            draw_line = none_line_streak > 2
            if draw_line:
                none_line_streak = 0
        
        if draw_line:
            # Lets do the work.
            for xpos in range(range_x, -1, -1):
                # Check if we're in range of the grid.
                if xpos <= width and start_y <= height:
                    if 0 <= xpos < max_x and 0 <= start_y < max_y:
                        runtime.SVG.illusion_array[start_y][xpos] = '*'
                                
                start_y += 1

#
# Write the Final SVG File from Data in the List.
#
# TODO: Refactor to accept canvas size and data as parameters for testability
# TODO: Externalise header and root <svg> attributes for templating flexibility
def svg_savefile(savename):
    """
    Save the SVG content to a file using current canvas dimensions and data.

    This function uses global canvas size values and the accumulated SVG output
    list, and writes the final SVG file to disk with proper error handling.

    Args:
        savename (str): Output path and filename for the SVG file.

    Returns:
        None. Writes the file to disk.

    Globals:
        SVG.canvas_width (float): Width of the canvas in mm.
        SVG.canvas_height (float): Height of the canvas in mm.
        SVG.data_list (list[str]): List of SVG fragments to embed in the final file.
        SVG_HEADER (str): XML + DOCTYPE declaration.
        DEBUG (bool): Controls detailed error output.
    """

    try:
        output_path = Path(savename).resolve()

        with output_path.open('w', encoding="utf-8") as fp:
            fp.write(SVG_HEADER)
            fp.write(f'<svg width="{runtime.SVG.canvas_width:.2f}mm" height="{runtime.SVG.canvas_height:.2f}mm" xmlns="http://www.w3.org/2000/svg">\n')
            fp.write(''.join(runtime.SVG.data_list))
            fp.write('</svg>\n')

        print(f"\n✅ Written file: {output_path}")

    except PermissionError as error:
        print(f"❌ Permission denied when writing to {savename}. Is it open in another application?")
        if runtime.DEBUG:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
    except IOError as error:
        print(f"❌ File I/O error: {error}")
        if runtime.DEBUG:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
    except Exception as error:
        print(f"❌ Unexpected error: {error}")
        if runtime.DEBUG:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)


#
# Update Canvas Width/Height
#
# TODO: Remove or explain the `if width > 405: print` line
# TODO: Consider returning updated dimensions instead of using globals
def update_svg_canvas_dimensions(width, height):
    """
    Update the global SVG canvas dimensions if the new dimensions are larger.

    This ensures that the final SVG canvas is large enough to accommodate all
    generated elements across multiple operations.

    Args:
        width (float): Proposed new canvas width in mm.
        height (float): Proposed new canvas height in mm.

    Returns:
        None. Modifies global variables in-place.

    Globals:
        SVG.canvas_width (float): Current maximum canvas width.
        SVG.canvas_height (float): Current maximum canvas height.
    """

    if width > runtime.SVG.canvas_width:
        runtime.SVG.canvas_width = width

    if height > runtime.SVG.canvas_height:
        runtime.SVG.canvas_height = height

#
# Create an SVG File sized for the Range 400mm Frames
#   Current loading is the internal frame has a useable 397mm
#       with 405mm on outer frame before backing board.
#
def create_svg_frame400(Outline_Only = True, 
                        add_PNG = False, 
                        rect_radius_x = 25, 
                        rect_radius_y = 25):
    """
    Create SVG data and cut guides for mounting art in a 400mm x 400mm frame (as sold by The Range).

    The layout includes:
    - Usable inner area: 397mm x 397mm
    - Outer mount board size: 405mm x 405mm
    - Optional background and corner radius parameters
    - Optional PNG layer
    - Optional cut guides for MAPED mountboard cutter

    Args:
        Outline_Only (bool): If True, suppress SVG fill elements and render only outlines.
        add_PNG (bool): If True, include the in-memory PNG rendering into the layout.
        rect_radius_x (float): Horizontal corner radius as a percentage.
        rect_radius_y (float): Vertical corner radius as a percentage.

    Globals:
        Image_Real_Width (int): Width of the loaded PNG in pixels.
        Image_Real_Height (int): Height of the loaded PNG in pixels.
        SVG.canvas_width (float): Used when placing cut guides.
        SVG.canvas_height (float): Used when placing cut guides.
        SVG.data_list (list[str]): Appended with SVG group markup for cut guides.

    Returns:
        None. Appends formatted SVG elements directly to SVG.data_list.

    TODO:
        - Generalise for other frame sizes (currently hardcoded to 400mm/405mm)
        - Accept frame model name or dimensions as input
        - Consider separating visual elements and guide logic
    """

    # Useable Area of the Frame
    useableArea = 397.00
    outerFrame  = 405.00

    # Get the number of Pixels plus border of 2
    if runtime.IMAGE.real_width > 0:
        multiplier = int(max (runtime.IMAGE.real_width + 4, runtime.IMAGE.real_height + 4))
        if multiplier < 20: 
            multiplier = 20
        rect_width = useableArea / multiplier
        rect_height = rect_width

    
    # Calculate the real width

    offset = (outerFrame - useableArea) / 2

    print(" Actual dimensions for 400mm Frame are :")
    print("----------------------------------------")
    print(f"       Internal Frame : {useableArea}mm x {useableArea}mm")
    print(f"          Outer Frame : {outerFrame}mm x {outerFrame}mm")
    print(f"   Pixel Width/Height : {rect_width:.2f}mm x {rect_height:.2f}mm")
    #print(f"          Rect Radius : {args.svg_radius_percent_x:.2f}% x {args.svg_radius_percent_y:.2f}%")
    print(f"          Rect Radius : {rect_radius_x:.2f}% x {rect_radius_y:.2f}%")


    create_svg(multiplier, multiplier, Outline_Only,  True, add_PNG, offset, offset, rect_width, rect_height, rect_radius_x, rect_radius_y )


    # Create the CUT Guides, I'm using the MAPED Mountboard Cutter, the Straight Edge needs
    # a 60mm Offset from bottom of the ruler to the cutting point of the blade.
    # You need 70mm if you're planning on using the 45 Degree Bevel Cutter.
    CutGuides = [f'\t<g id="CutGuidesGroup"> \n']
    
    # Add 400mm border
    CutGuides.append(add_svg_rectangle("Card Border",0.0, 0.0, 405.0, 405.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))

    # Add Maped Cutter Marks
    CutGuides.append(add_svg_rectangle("TopLeftGuide",0.0, 0.0, 60.0, 60.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))
    CutGuides.append(add_svg_rectangle("TopRightGuide",runtime.SVG.canvas_width - 60.0, 0.0, 60.0, 60.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))
    CutGuides.append(add_svg_rectangle("BottonLeftGuide",0.0, runtime.SVG.canvas_height - 60.0, 60.0, 60.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))
    CutGuides.append(add_svg_rectangle("BottomRightGuide",runtime.SVG.canvas_width - 60.0, runtime.SVG.canvas_height - 60.0, 60.0, 60.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))

    CutGuides.append(f'\t</g>\n')

    runtime.SVG.data_list.append(''.join(CutGuides))



#
# Create and Write an SVG Object to File with the Square Optical Illusion.
#   savename        : Filename to Write
#   width           : Width in pixels   (Number of Rectangles Wide)
#   height          : Height in Pixels  (Number of Rectangles High)
#   add_PNG         : Add the PNG loaded in Memory?, Default = No
#   startX          : X Position Offset Start , Default = 0.0mm
#   startY          : Y Position Offset Start , Default = 0.0 mm
#   rect_width      : Width of Rectangles , Default = 20.0mm
#   rect_height     : Height of Rectangles, Default = 20.0mm
#   rect_radius_X   : Corner Radius on X  , Default = 25%
#   rect_radius_Y   : Corner Radius on Y  , Default = 25%
#
def create_svg(width, height, 
               outline_only, 
               use_real_colours = True, 
               add_PNG = False, 
               startX = 0.0, startY = 0.0, 
               rect_width=20.0, rect_height=20.0, 
               rect_radius_x = 25.0, rect_radius_y = 25.0):
    """
    Create optical illusion-style SVG data using either diagonal or circular patterns.

    Optionally overlays a sprite image (from loaded PNG) and includes calculated offsets 
    and styling based on real-world dimensions.

    Args:
        width (int): Grid width in number of rectangles.
        height (int): Grid height in number of rectangles.
        outline_only (bool): If True, omits fill colours and only renders borders.
        use_real_colours (bool): If True, retains original pixel colour information.
        add_PNG (bool): If True, overlays a sprite image onto the SVG illusion.
        startX (float): Starting X offset in mm.
        startY (float): Starting Y offset in mm.
        rect_width (float): Width of each rectangle in mm.
        rect_height (float): Height of each rectangle in mm.
        rect_radius_x (float): Corner radius X (% of width).
        rect_radius_y (float): Corner radius Y (% of height).

    Returns:
        None. Appends data directly to SVG.data_list.

    Globals:
        SVG.data_list (list[str]): The main buffer collecting final SVG fragment data.
        SVG.illusion_type_circle (bool): Switch between circular vs diagonal grid illusion.
        Image_Real_Width (int): Width of loaded PNG (for offsetting sprite overlay).
        Image_Real_Height (int): Height of loaded PNG.

    TODO:
        - Parameterise illusion type via argument instead of global
        - Add validation for grid/offset sizes
        - Split fill/light/dark logic into helper functions
    """

    totalWidth = rect_width * width + abs(startX * 2)
    totalHeight = rect_height * height + abs(startY * 2)

    # Update the Canvas size, just incase...     
    update_svg_canvas_dimensions(totalWidth, totalHeight)


    # Create Illusion Data
    if runtime.SVG.illusion_type_circle:
        fill_group, light_group, dark_group = create_svg_illusion_data_circular(outline_only,
                                                                                width, height,
                                                                                rect_width, rect_height,
                                                                                rect_radius_x, rect_radius_y,
                                                                                startX, startY)
    else:
        fill_group, light_group, dark_group = create_svg_illusion_data_diagonals(outline_only,
                                                                                 width, height,
                                                                                 rect_width, rect_height,
                                                                                 rect_radius_x, rect_radius_y,
                                                                                 startX, startY)

    if not outline_only:
        runtime.SVG.data_list.append(''.join(fill_group))

    runtime.SVG.data_list.append(''.join(dark_group))
    runtime.SVG.data_list.append(''.join(light_group))

    if add_PNG:
        offsetX = math.ceil((width - runtime.IMAGE.real_width) / 2)
        offsetY = math.ceil((height - runtime.IMAGE.real_height) / 2)
        sprite_Data = create_svg_data_for_loaded_PNG(outline_only, use_real_colours,
                                                     offsetX, offsetY,
                                                     rect_width , rect_height,
                                                     rect_radius_x, rect_radius_y,
                                                     startX, startY)
        runtime.SVG.data_list.append(''.join(sprite_Data))

#
# Create SVG Data for the Optical Illusion
#
def create_svg_rect_Grid(outline_only = False,
                         width = 20, height = 20,
                         rect_width=20.0, rect_height=20.0,
                         rect_radius_x = 25, rect_radius_y = 25,
                         offsetX = 0.0, offsetY = 0.0,
                         fillcolour1 = "#020078",
                         fillcolour2 = "#3F53FF"):
    """
    Generate a rectangular grid of SVG <rect> elements, with alternating fill colours.

    Used to build visual background or illusion patterns by alternating between two
    colour values and separating them into 'light' and 'dark' groups.

    Args:
        outline_only (bool): If True, disables fill and applies stroke-only style.
        width (int): Number of rectangles across the X-axis.
        height (int): Number of rectangles down the Y-axis.
        rect_width (float): Width of each rectangle in mm.
        rect_height (float): Height of each rectangle in mm.
        rect_radius_x (float): Rounded corner radius X (%).
        rect_radius_y (float): Rounded corner radius Y (%).
        offsetX (float): Horizontal offset in mm.
        offsetY (float): Vertical offset in mm.
        fillcolour1 (str): Primary colour hex code.
        fillcolour2 (str): Secondary colour hex code.

    Returns:
        tuple: Two lists of SVG strings — (light_group, dark_group)

    Globals:
        SVG.grid_count (int): Tracks total number of rectangles generated.

    TODO:
        - Consider splitting light/dark group logic into a reusable helper
        - Allow `fillcolour1` and `fillcolour2` to accept lists for multi-colour cycling
        - Evaluate performance on very large grids
    """
    # Dark and Light Groups
    dark_group = ['\t<g id="DarkGroup">\n']
    light_group = ['\t<g id="LightGroup">\n']

    for y in range(int(height)):
        current_y = (y * rect_height) + offsetY
        for x in range(int(width)):
            current_x = (x * rect_width) + offsetX
            fill_color = fillcolour1 if (x % 2) == (y % 2) else fillcolour2

            # Generate random base values for RGB within the range 0-63
            #r, g, b = [random.randint(0, 63) for _ in range(3)]

            # Determine the offset based on the parity of x and y
            #offset = 16 if (x % 2) == (y % 2) else 164

            # Apply the offset to each color component
            #r, g, b = [value + offset for value in (r, g, b)]

            # Format the final color as a hex string
            #fill_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
            
            group = dark_group if fill_color == fillcolour1 else light_group

            if not outline_only:
                newObj = add_svg_rectangle("",current_x, current_y, rect_width, rect_height, rect_radius_x, rect_radius_y, fill_color)
            else:
                newObj = add_svg_rectangle("",current_x, current_y, rect_width, rect_height, rect_radius_x, rect_radius_y, fill_color, 0, 0.25)
            
            group.append(newObj)
            runtime.SVG.grid_count += 1

    dark_group.append("\t</g>\n")
    light_group.append("\t</g>\n")

    return light_group, dark_group

#
# clip the coords for inside the canvas.
#
def ClipDimensions(rect_x, rect_y, rect_width, rect_height, offsetX, offsetY):
    """
    Clip a rectangle's dimensions to ensure it stays within the valid SVG canvas boundaries.

    This function adjusts the rectangle's position and size based on the provided offset
    and current global SVG canvas dimensions.

    Args:
        rect_x (float): X-coordinate of the rectangle's top-left corner.
        rect_y (float): Y-coordinate of the rectangle's top-left corner.
        rect_width (float): Requested width of the rectangle in mm.
        rect_height (float): Requested height of the rectangle in mm.
        offsetX (float): Horizontal margin in mm.
        offsetY (float): Vertical margin in mm.

    Returns:
        tuple: (adjusted_x, adjusted_y, clipped_width, clipped_height)

    Globals:
        SVG.canvas_width (float): Total width of the SVG canvas.
        SVG.canvas_height (float): Total height of the SVG canvas.

    TODO:
        - Move SVG.canvas_width/HEIGHT to parameters for testability
        - Document caller behaviour for rectangles that get fully clipped
    """
    req_width = rect_width
    req_height = rect_height

    # Clip Illusion Squares to image when in frame mode.
    if rect_x < offsetX:
        rect_x = offsetX
        req_width = rect_width - offsetX

    if rect_x + req_width > runtime.SVG.canvas_width - offsetX:
        req_width = runtime.SVG.canvas_width - offsetX - rect_x

    if rect_y < offsetY:
        rect_y = offsetY
        req_height= rect_height - offsetY

    if rect_y + req_height > runtime.SVG.canvas_height - offsetY:
        req_height = runtime.SVG.canvas_height - offsetY - rect_y

    return rect_x, rect_y, req_width, req_height


#
# Create SVG Data for the Optical Illusion - circles...
#
def create_svg_illusion_data_circular(outline_only = False, width = 20, height = 20, rect_width=20.0, rect_height=20.0, rect_radius_x = "25%", rect_radius_y = "25%", offsetX = 0.0, offsetY = 0.0):
    """
    Generate an SVG data grid with a circular optical illusion effect using concentric raster lines.
    
    Alternates between visible and skipped circles to create a vibration-like illusion.

    Args:
        outline_only (bool): If True, disables fill and renders stroke-only rectangles.
        width (int): Grid width in cells.
        height (int): Grid height in cells.
        rect_width (float): Width of each rectangle in mm.
        rect_height (float): Height of each rectangle in mm.
        rect_radius_x (str): Corner rounding percentage on X (e.g., "25%").
        rect_radius_y (str): Corner rounding percentage on Y (e.g., "25%").
        offsetX (float): Horizontal offset in mm.
        offsetY (float): Vertical offset in mm.

    Returns:
        tuple: (fill_group, light_group, dark_group) — SVG <g> sections.

    Globals:
        SVG.illusion_array (list): 2D array of raster pattern.
        SVG.dark_count (int): Total number of dark illusion blocks drawn.
        SVG.light_count (int): Total number of light blocks.
        SVG.illusion_max_streak (int): Max run of lines before toggling.
        SVG.illusion_colour_table (list): Colour palette.
        DARK_BLOCK_INDEX (int): Index of dark block colour.
        LIGHT_BLOCK_INDEX (int): Index of light block colour.

    TODO:
        - Parameterise SVG.illusion_max_streak instead of relying on global
        - Move ClipDimensions() and rectangle calc into reusable helper
        - Refactor to separate illusion generation from rendering loop
    """

    width = int(width)
    height = int(height)

    size = max(width, height)
    runtime.SVG.illusion_array = create_array(size)

    # Centre Point of Array
    cx = width / 2
    cy = height / 2

    # Main Optical Illusion Drawing Group
    fill_group = [f'\t<g id="OpticalIllusionGroup">\n']
    
    half_rect_width = (rect_width / 2)
    half_rect_height = (rect_height / 2)

    totalWidth = rect_width * width + abs(offsetX)
    totalHeight = rect_height * height + abs(offsetY)
    update_svg_canvas_dimensions(totalWidth, totalHeight)

    #
    # Create Circles of Data in Array
    #
    circle_streak = none_circle_streak = 0
    draw_circles = False

    max_radius = width + height
    circle_streak = none_circle_streak = 0

    for radius in range(max_radius):
        rand = random.randint(0,10)

        if rand > 3:
            circle_streak, none_circle_streak = circle_streak + 1, 0
            draw_circles = circle_streak < runtime.SVG.illusion_max_streak
            if not draw_circles:
                circle_streak = 0
                none_circle_streak = 1
        else:
            none_circle_streak, circle_streak = none_circle_streak + 1, 0
            draw_circles = none_circle_streak > runtime.SVG.illusion_max_streak
            if draw_circles:
                circle_streak = 1
                none_circle_streak = 0

        if draw_circles:
            draw_circle(runtime.SVG.illusion_array, cx, cy, radius)

    print_array(runtime.SVG.illusion_array)

    fill_group = [f'\t<g id="OpticalIllusionCirclesAll">\n']
    for y in range (height):
        for x in range(width):
            sample = runtime.SVG.illusion_array[y][x]
            if sample != " ":
                fillColour = "#000000"
                runtime.SVG.dark_count += 1
            else:
                fillColour = "#ffffff"
                runtime.SVG.light_count += 1
                    
            rect_x = x * rect_width - half_rect_width + offsetX
            rect_y = y * rect_height - half_rect_height + offsetY

            rect_x, rect_y, req_width, req_height = ClipDimensions(rect_x, rect_y, rect_width, rect_height, offsetX, offsetY)
                
            if not outline_only:
                newObj = add_svg_rectangle("",rect_x, rect_y,req_width, req_height, 0, 0, fillColour)
            else:
                newObj = add_svg_rectangle("",rect_x, rect_y,req_width, req_height, 0, 0, fillColour, 0, 0.5)
            fill_group.append(newObj)

    fill_group.append('\t</g>\n')

    light_group, dark_group = create_svg_rect_Grid(outline_only, 
                                                   width, height,
                                                   rect_width, rect_height,
                                                   rect_radius_x, rect_radius_y,
                                                   offsetX, offsetY,
                                                   runtime.SVG.illusion_colour_table[DARK_BLOCK_INDEX],
                                                   runtime.SVG.illusion_colour_table[LIGHT_BLOCK_INDEX])
 
    return fill_group, light_group, dark_group


#
# Create SVG Data for the Optical Illusion
#
def create_svg_illusion_data_diagonals(outline_only = False, width = 20, height = 20, rect_width=20.0, rect_height=20.0, rect_radius_x = "25%", rect_radius_y = "25%", offsetX = 0.0, offsetY = 0.0):
    """
    Generate SVG illusion data based on diagonal line patterns.

    Creates a grid of rectangles where each diagonal is conditionally filled or skipped
    to produce a wobble or flicker illusion effect. The output is structured in groups
    labelled by coordinate for post-processing or SVG manipulation.

    Args:
        outline_only (bool): If True, uses stroke-only rectangles.
        width (int): Number of rectangles across.
        height (int): Number of rectangles down.
        rect_width (float): Width of each rectangle in mm.
        rect_height (float): Height of each rectangle in mm.
        rect_radius_x (str): Horizontal corner radius as percentage string.
        rect_radius_y (str): Vertical corner radius as percentage string.
        offsetX (float): Horizontal grid offset.
        offsetY (float): Vertical grid offset.

    Returns:
        tuple: (fill_group, light_group, dark_group)

    Globals:
        SVG.dark_count (int): Counter for dark block rectangles.
        SVG.light_count (int): Counter for light block rectangles.
        SVG.illusion_colour_table (list[str]): Colour options.
        SVG.illusion_max_streak (int): Controls visual rhythm of the pattern.

    TODO:
        - Add parameter to control diagonal direction (currently fixed)
        - Refactor inner loop and draw decision logic into helper
        - Consider exposing fill/stroke style per-diagonal group
    """

    width = int(width)
    height = int(height)

    # Loop Counter to ensure we get all diagonals.
    max_range = int(width + height + 1)

    # Main Optical Illusion Drawing Group
    fill_group = [f'\t<g id="OpticalIllusionGroup">\n']

    half_rect_width = rect_width / 2
    half_rect_height = rect_height / 2

    totalWidth = rect_width * width + abs(offsetX)
    totalHeight = rect_height * height + abs(offsetY)
    update_svg_canvas_dimensions(totalWidth, totalHeight)


    light_group, dark_group = create_svg_rect_Grid(outline_only,
                                                   width, height, rect_width, rect_height,
                                                   rect_radius_x, rect_radius_y,
                                                   offsetX, offsetY,
                                                   runtime.SVG.illusion_colour_table[DARK_BLOCK_INDEX],
                                                   runtime.SVG.illusion_colour_table[LIGHT_BLOCK_INDEX])

    if outline_only:
        return [], light_group, dark_group

    line_streak = none_line_streak = 0
    draw_line = False

    # Loop Across the Object
    for x in range(max_range):
        # The Start Y Position will typically be Zero, when it moves to the right of the Width, 
        # We start offseting the Y position on Grid to be max Width, Y = 0 -> HEIGHT
        # Just a trick without additional loops.
        # range_x is fixed to all columns up to maximum column width
        start_y = int(max(0, x - width))
        range_x = int(min(x, width))
        
        # Label up each of the Diagonal Groups with their start X,Y Coords
        # Diagonals set from Top Right to Bottom Left
        fill_group.append(f'\t\t<g id="DiagonalGroup{range_x}:{start_y}">\n')
        # Set a random Colour
        rand = random.randint(0, 10)
        fill_color = (
            "#000000" if rand <= 7 else
            "#ffffff"
        )

        # Determine if a diagonal line should be drawn

        # Try Black if greater than five and less than streak
        if rand > 5:
            line_streak, none_line_streak = line_streak + 1, 0
            draw_line = line_streak <= runtime.SVG.illusion_max_streak
            if not draw_line:
                line_streak = 0
                none_line_streak = 1
                #draw_line = True
        else:
            none_line_streak, line_streak = none_line_streak + 1, 0
            draw_line = none_line_streak > runtime.SVG.illusion_max_streak
            if draw_line:
                line_streak = 1
                none_line_streak = 0
                draw_line = True

        
        fill_color = (
            "#000000" if draw_line else
            "#ffffff"
        )

        # Lets do the work.
        for xpos in range(range_x, -1, -1):
            # Check if we're in range of the grid.
            if xpos <= width and start_y <= height:
                rect_x = xpos * rect_width - half_rect_width + offsetX
                rect_y = start_y * rect_height - half_rect_height + offsetY


                rect_x, rect_y, req_width, req_height = ClipDimensions(rect_x, rect_y, rect_width, rect_height, offsetX, offsetY)
                

                if draw_line:
                    runtime.SVG.dark_count += 1
                else:
                    runtime.SVG.light_count += 1

                if not outline_only:
                    newObj = '\t'+add_svg_rectangle("",rect_x, rect_y,
                                                    req_width, req_height,
                                                    0, 0, fill_color)
                else:
                    newObj = '\t'+add_svg_rectangle("",rect_x, rect_y,
                                                    req_width, req_height,
                                                    0, 0, fill_color, 0, 1.0)

                fill_group.append(newObj)
                start_y += 1

        fill_group.append('\t\t</g>\n')

    fill_group.append('\t</g>\n')

    return fill_group, light_group, dark_group

#
# Create and Write an SVG Object to File with the Square Optical Illusion.
#
def create_svg_from_PNG(outlineOnly, use_real_colours,
                        rect_width=20.0, rect_height=20.0,
                        rect_radius_x = 25.0, rect_radius_y = 25.0,
                        startX = 0.0, startY = 0.0):
    """
    Create SVG elements that represent each pixel of the loaded PNG image.

    This function prepares an SVG sprite layer by converting pixel positions into
    rounded rectangles (or outlines only). It sets up the canvas size and calls a
    lower-level function to generate the actual drawing instructions.

    Args:
        outlineOnly (bool): If True, renders stroke outlines only.
        use_real_colours (bool): If False, substitutes pixel colours with illusion palette.
        rect_width (float): Width of each rectangle in mm.
        rect_height (float): Height of each rectangle in mm.
        rect_radius_x (float): Rounded corner radius on the X axis (%).
        rect_radius_y (float): Rounded corner radius on the Y axis (%).
        startX (float): Horizontal shift in mm.
        startY (float): Vertical shift in mm.

    Returns:
        None. Appends SVG group content to the global SVG.data_list.

    Globals:
        SVG.data_list (list[str]): Aggregates the visual content of the SVG output.
        Image_Real_Width (int): Pixel width of loaded PNG.
        Image_Real_Height (int): Pixel height of loaded PNG.

    TODO:
        - Consider returning the generated SVG group instead of appending globally
        - Parameterise input pattern image instead of assuming current global
    """

    width = runtime.IMAGE.real_width
    height = runtime.IMAGE.real_height

    totalWidth = rect_width * width + abs(startX)
    totalHeight = rect_height * height + abs(startY)
    update_svg_canvas_dimensions(totalWidth, totalHeight)

    # Main Optical Illusion Drawing Group
    sprite_group = create_svg_data_for_loaded_PNG(outlineOnly,
                                                  use_real_colours,
                                                  startX, startY,
                                                  rect_width, rect_height,
                                                  rect_radius_x, rect_radius_y)

    runtime.SVG.data_list.append(''.join(sprite_group))

#
# Create SVG Data for currently Loaded PNG In memory.
#
def create_svg_data_for_loaded_PNG(outline_only = False,
                                   use_real_colours = True,
                                   offset_X = 0.0, offset_Y = 0.0,
                                   rect_width=20.0, rect_height=20.0,
                                   rect_radius_x = "25%",
                                   rect_radius_y = "25%",
                                   start_X = 0.0, start_Y = 0.0):
    """
    Create SVG data corresponding to each pixel of the loaded PNG image.

    This function overlays the sprite or image grid based on real pixel data,
    mapped to a rectangular tile grid for scalable printing or cutting. Optionally
    uses alternating colours instead of real colours to produce illusions.

    Args:
        outline_only (bool): If True, draws outlines only (circles or text instead of rectangles).
        use_real_colours (bool): If False, replaces real colours with illusion palette.
        offset_X (float): Horizontal shift of pixel grid in grid units.
        offset_Y (float): Vertical shift of pixel grid in grid units.
        rect_width (float): Width of each grid cell in mm.
        rect_height (float): Height of each grid cell in mm.
        rect_radius_x (str): Corner radius X (percentage).
        rect_radius_y (str): Corner radius Y (percentage).
        start_X (float): Additional horizontal offset in mm.
        start_Y (float): Additional vertical offset in mm.

    Returns:
        list[str]: List of SVG fragment strings forming the sprite overlay group.

    Globals:
        SVG.png_pixel_count (int): Accumulates the number of drawn pixels.
        pattern, pattern_w, pattern_h: Used to read and wrap pixel data.
        Image_MinX, Image_MinY, Image_Real_Width, Image_Real_Height: Sprite dimensions.
        SVG.illusion_colour_table: Used when not using real colours.
        DARK_PIXEL_INDEX, LIGHT_PIXEL_INDEX: Used to alternate colour blocks.

    TODO:
        - Move `pattern`/image data to passed parameters
        - Consider merging sprite draw logic into generalised SVG pixel engine
        - Add opacity toggle or pixel thresholding
    """
    
    width = runtime.IMAGE.real_width
    height = runtime.IMAGE.real_height

    half_w = rect_width / 2
    half_h = rect_height / 2
    
    totalWidth = (rect_width * width) + offset_X + abs(start_X)
    totalHeight = rect_height * (height + offset_Y) + abs(start_Y)

    update_svg_canvas_dimensions(totalWidth, totalHeight)

    # Main Optical Illusion Drawing Group
    sprite_group = ['\t<g id="SpriteImage">\n']

    radius_size = min(rect_width, rect_height) * 0.25
    
    dark_group = ['\t\t<g id="DarkPNGGroup">\n']
    light_group = ['\t\t<g id="LightPNGGroup">\n']
    
    # Loop Across the Object
    for y in range(height):
        row = runtime.IMAGE.pattern[int((y+runtime.IMAGE.min_y) % runtime.IMAGE.height)]
        for x in range(width):
            pixel, index, fill_color = getPixelFromRow(x + runtime.IMAGE.min_x,row,runtime.IMAGE.channels, runtime.IMAGE.width )
            # Only Add Pixel if in the Allowed Colour List
            if pixel >=0:
                if not use_real_colours:
                    #fill_color = "#2f0040" if (x % 2) == (y % 2) else "#FF7f80"
                    fill_color = runtime.SVG.illusion_colour_table[DARK_PIXEL_INDEX] if ((x+offset_X) % 2) == ((y+offset_Y) % 2) else runtime.SVG.illusion_colour_table[LIGHT_PIXEL_INDEX]
                    group = dark_group if (x % 2) == (y % 2) else light_group

                rect_x = (x + offset_X) * rect_width + start_X
                rect_y = (y + offset_Y) * rect_height + start_Y

                runtime.SVG.png_pixel_count += 1
                if not outline_only:
                    newObj = add_svg_rectangle("",rect_x, rect_y, rect_width, rect_height, rect_radius_x, rect_radius_y, fill_color)
                else:
                    #newObj = add_svg_centeredText(rect_x + half_w, rect_y + half_h, "X", "#000000")
                    newObj = add_svg_centeredCircle(rect_x + half_w, rect_y + half_h, radius_size, "none", 1)

                if use_real_colours:
                    sprite_group.append(newObj)
                else:
                    group.append("\t"+newObj)
    if not use_real_colours:
        dark_group.append("\t\t</g>\n")
        light_group.append("\t\t</g>\n")
        sprite_group.append(''.join(dark_group))
        sprite_group.append(''.join(light_group))
    
    sprite_group.append('\t</g>\n')

    return sprite_group

#
# Create a Primitive, in this example a Cube, but could be swapped for
# Any primitive type
#
def create_primitive(primitive_x, primitive_y,
                     width, height,
                     primitive_vert,
                     primitive_face,
                     primitive_normals,
                     jointFlag, material_index,
                     primitive_y_multiplier=1.0,
                     modify_Flag = True):
    """
    Construct the OBJ data string for a single primitive (pixel/cube section).

    including vertex definitions, normals, and faces. Supports optional extrusion,
    join alignment logic, and material tagging.

    Args:
        primitive_x (int): X index in the pixel grid.
        primitive_y (int): Y index in the pixel grid.
        width (int): Width multiplier (usually 1).
        height (int): Height multiplier (usually 1).
        primitive_vert (list): List of vertex coordinate tuples.
        primitive_face (list): List of face definitions (each a list of vertex indices).
        primitive_normals (list): List of normal vectors.
        jointFlag (int or bool): If non-zero, alters how joining faces are placed.
        material_index (int): Material ID for usemtl.
        primitive_y_multiplier (float): Used to scale Z for height illusion effects.
        modify_Flag (bool): If True, apply bounding adjustments using `update_vert`.

    Returns:
        str: OBJ-format string containing vertex, normal, face, and material lines.

    Globals:
        Current_Face (int): Running counter for face IDs.
        Current_Opposite_Face (int): Offset for alternate normal indexing.
        CurrentZOffset (float): Z-axis depth accumulator.
        CUBE_X, CUBE_Y (float): Global size constants.
        Primitive_Layer_Depth (float): Used in Z extrusion.
        Primitive_Multipler (float): Overall pixel-to-mm scale.
        CREATE_MTL_FILE (bool): Controls whether to emit `mtllib` / `usemtl`.
        mtl_filename (str): File basename for MTL reference.

    TODO:
        - Clean up legacy commented face logic
        - Clarify jointFlag meaning and ensure 0/1 vs signed int is consistent
        - Replace raw string formatting with f-string block builders for clarity
        - Split into helper functions for face block, normal block, and vertex block
    """

  #  if not jointFlag:
  #      return ""

    strVertices = f"o Pixel_{primitive_x}_{primitive_y}\n"
    strFaces = ""

    # Get the number of entries for Cube Vertices
    # For future where primitive may change
    vert_len = len(primitive_vert)
    face_len = len(primitive_face)

    rx = primitive_x * runtime.CUBE_X * runtime.Primitive_Multipler
    ry = primitive_y * runtime.CUBE_Y * runtime.Primitive_Multipler
    rx2 = rx + (runtime.CUBE_X * width * runtime.Primitive_Multipler)
    ry2 = ry + (runtime.CUBE_Y * height * runtime.Primitive_Multipler)

    myFormatter = "{0:.6f}"

    #
    # Generate the Basic Primitive for the Model
    #
    for index in range(vert_len):
        v1 = primitive_vert[index][0] * runtime.Primitive_Multipler
        v2 = primitive_vert[index][1] * runtime.Primitive_Multipler
        v3 = primitive_vert[index][2] * (runtime.Primitive_Layer_Depth/10) #* Primitive_Multipler

        if v3 != 0.0 and primitive_y_multiplier != 1.0:
            v4 = primitive_y_multiplier * v3
            v3 = v4 + runtime.CurrentZOffset
        else:
            v3 += runtime.CurrentZOffset

        # Yeah, quick and dirty, I need to think this through
        if not jointFlag:
            if modify_Flag:
                v1 = update_vert(v1, rx, rx2)
                v2 = update_vert(v2, ry, ry2)

        else:
            # Invert Jointer Piece Depending on Direction set
            v1 = (jointFlag * v1) + rx + (runtime.CUBE_X * runtime.Primitive_Multipler)
            v2 = v2 + ry

        strVertices = strVertices + "v " + str(myFormatter.format(v1)) + " " + \
                        str(myFormatter.format(v2)) + " " + str(myFormatter.format(v3)) + "\n"

    strVertices = strVertices + "# "+str(vert_len)+f" Vertices\n"

    strNormals = ""
    # Bit of a Bodge... 
    for index in range(len(primitive_normals)):
        n1 = primitive_normals[index][0]
        n2 = primitive_normals[index][1]
        n3 = primitive_normals[index][2]
        strNormals = strNormals + "vn " + str(myFormatter.format(n1)) + " " + str(myFormatter.format(n2)) + " " + str(myFormatter.format(n3)) + "\n"

    strNormals = strNormals + "# "+str(len(primitive_normals))+f" Normals\n"

    #strFaces = "# "+str(vert_len)+f" Vertices\ng Pixel_{primitive_x}_{primitive_y}_F\n"
    mtl_string=""

    if runtime.CREATE_MTL_FILE:
        mtl_string = "mtllib "+os.path.basename(runtime.mtl_filename) + "\n" + \
            f"usemtl {material_index}\n"

    strFaces=f"g ACIS Pixel_{primitive_x}_{primitive_y}_F\n"

    #
    # Face List may contain variable length face lists.
    #
    for index in range(face_len):
        # Initial Face Identifier
        strFaces = strFaces + "f "

        for faceIndex in range(len(primitive_face[index])):
            
            faceID = primitive_face[index][faceIndex] + runtime.Current_Face
            faceIDOpposite = runtime.Current_Opposite_Face+faceID
            if jointFlag:
                strFaces = strFaces + f"{faceID}//{faceIDOpposite} "
            else:
                strFaces = strFaces + f"{faceID}//{faceID} "
            #f1 = primitive_face[index][0] + Current_Face
            #f2 = primitive_face[index][1] + Current_Face
            #f3 = primitive_face[index][2] + Current_Face

            #strFaces = strFaces + "f " + f"{f1}//{f1} {f2}//{f2} {f3}//{f3}\n"
            #if jointFlag:
            #    strFaces = strFaces + "f " + f"{f1}//{Current_Opposite_Face + f1} {f2}//{Current_Opposite_Face + f2} {f3}//{Current_Opposite_Face + f3}\n"
            #else:
                #strFaces = strFaces + "f " + f"{f1}//{(index*3)+1+ Current_Opposite_Face} {f2}//{(index*3)+2+ Current_Opposite_Face} {f3}//{(index*3)+3+ Current_Opposite_Face}\n"
            #    strFaces = strFaces + "f " + f"{f1}//{f1} {f2}//{f2} {f3}//{f3}\n"

        strFaces = strFaces + "\n"

    Primitive_String = strVertices + strNormals + mtl_string + strFaces + "# "+str(face_len)+" Faces\n\n"


    # update face Index Counter to next set 
    #Current_Face += (face_len * 2)
    #Current_Face += 8
    runtime.Current_Face += len(primitive_vert)
    runtime.Current_Opposite_Face += (len(primitive_normals))
    return Primitive_String

#
# And this is where all that magic happens.
#   A real Python Programmer can probably optimise this using some Python Magic.
#
def main(noframeRequired):
    """
    Execute the main program logic for layered PNG-to-OBJ conversion.

    Depending on the selected mode, this function optionally generates a flat background layer,
    sorts colour layers by count or explicit order, filters colours based on inclusion/exclusion
    lists, and processes the image into multiple 3D printable OBJ layers.

    Args:
        noframeRequired (bool): If True, skips generating the flat background OBJ.

    Globals:
        WORKING_FILENAME (str): Base filename for output OBJ files.
        MATERIALS.exclusion (list[str]): Colours to skip.
        MATERIALS.process_only (list[str]): Colours to force inclusion.
        Sort_Colours_Flag (bool): Whether to sort colours by count.
        Sort_Direction (bool): If True, sort descending; otherwise ascending.
        FILE_COUNTER (int): Counter to track how many layers have been generated.
        Primitive_Multiplier_Background (float): Z depth multiplier for background layer.
        Primitive_Multiplier_Layers (float): Z depth multiplier for each coloured layer.
        Create_Layered_File (bool): Whether to generate OBJ per colour.
        ColoursOnSingleLayerHeight (bool): Treat all layers as same height.
        MATERIALS.colours (dict): Maps colour hex codes to pixel counts.

    Returns:
        None. Writes OBJ files to disk.
    
    TODO:
        - Move layer selection and sorting logic to a helper
        - Refactor background flat layer creation into `write_background_layer()`
        - Separate print output from logic for clean testing
    """

    # Create the Background Object File 
    # Flat Structure width and height of PNG Image.
    obj_file = os.path.join(runtime.PATTERNS, "{}.obj".format(runtime.WORKING_FILENAME))

    if not noframeRequired:
        try:
            # TODO: Add some error checking here, rather than rely on TRY/CATCH Scenarios.
            with open(obj_file,'w') as fp_obj:
                    fp_obj.write(create_primitive(0, 0, runtime.IMAGE.width, runtime.IMAGE.height, cube_vertices, cube_faces, cube_normals, 0, 0, runtime.Primitive_Multiplier_Background))
                    fp_obj.flush()
                    fp_obj.close()
                    # Update Current Offset with multiplier requested
                    #CurrentZOffset += (abs(CUBE_Y*Primitive_Multiplier_Background)) # Shift Vertices Up a Layer...
                    #CurrentZOffset += (abs(CUBE_Y*Primitive_Multiplier_Background*Primitive_Multipler)) # Shift Vertices Up a Layer...
                    runtime.CurrentZOffset += runtime.Primitive_Layer_Depth*runtime.Primitive_Multiplier_Background # Shift Vertices Up a Layer...
                
        except Exception as error:
        # Bad Practice I know...
            print(f"Failed to create Initial file: {obj_file}, error: {error}")
            sys.exit(1)


    ToSort = {}

    if len(runtime.MATERIALS.process_only) > 0:
        SortedColours = list(runtime.MATERIALS.process_only)
        for x in range(0,len(runtime.MATERIALS.process_only)):
            ToSort[runtime.MATERIALS.process_only[x]] = x
    else:
        # Set the Sorted Colours Dictionary to Default
        # Remove any layes that have no pixels
        # Colour layers that are all below the Alpha Threshold will have a count of 0
        for key in runtime.MATERIALS.colours:
            if runtime.MATERIALS.colours[key] > 0:
                ToSort[key] = runtime.MATERIALS.colours[key]
            else:
                print(f"Removing Colour: {key} from processing, pixel count of Zero Detected (Check Alpha Threshold If Required)")

    # Check if we want to sort by Highest Colour Count First
    if runtime.Sort_Colours_Flag:
        #SortedColours = {key: val for key, val in sorted(MATERIALS.colours.items(), key = lambda ele: ele[1], reverse=Sort_Direction)}
        SortedColours = {key: val for key, val in sorted(ToSort.items(), key = lambda ele: ele[1], reverse=runtime.Sort_Direction)}
    else:
        SortedColours = dict(ToSort)

    # Remove Colours from Excluded List 
    for excluded in runtime.MATERIALS.exclusion:
        if excluded in SortedColours:
            del SortedColours[excluded]

    print("Layer Order:")
    for nextLayer in SortedColours:
        print(f"{nextLayer}")

    print(f"       Found : {len(runtime.MATERIALS.colours)} Colours")
    print(f"Working with : {len(SortedColours)} Colours\n")

    runtime.FILE_COUNTER +=1

    if runtime.Create_Layered_File:
        while len(SortedColours) > 0:
            nextLayer = list(SortedColours.keys())[0]
            runtime.log(f"Processing Colour: {nextLayer}")

            if nextLayer in runtime.MATERIALS.colours:
                if runtime.ColoursOnSingleLayerHeight:
                    resp = processFile(nextLayer, nextLayer, runtime.MATERIALS.exclusion, runtime.Primitive_Multiplier_Layers)
                else:
                    resp = processFile(nextLayer, SortedColours, runtime.MATERIALS.exclusion, runtime.Primitive_Multiplier_Layers)
                
                if resp == False:
                    print("Failed to process file:")
                    sys.exit(1)
            else:
                print(f"Colour: {nextLayer} is not present, skipping...")
            # Add colour to excluded list to avoid repeat processing
            runtime.MATERIALS.exclusion+=[nextLayer]
            del SortedColours[nextLayer]
    else:
        resp = processFile(list(SortedColours.keys())[0], SortedColours, runtime.MATERIALS.exclusion)

def displayColourInformation():
    """
    Print a summary of all detected colours and their associated pixel counts.

    This function sorts the colours found in the loaded PNG based on how frequently
    they occur, and displays the hex code alongside the pixel count for each.

    Returns:
        None. Output is printed to stdout.

    Globals:
        MATERIALS.colours (dict): Dictionary mapping hex colour codes to pixel usage counts.

    TODO:
        - Add CSV or JSON export option for colour statistics
        - Allow filtering or sorting by hex code
        - Consider aligning this with layer preview generation
    """
    SortedColours = {key: val for key, val in sorted(runtime.MATERIALS.colours.items(), key = lambda ele: ele[1], reverse=True)}
    
    print("         Layer Order :")
    print("         -------------")
    print()
    print("         Colour Code : Number of Pixels")
    print("         -----------   ----------------\n")   
    for nextLayer in SortedColours:
        print(f"             {nextLayer} : {SortedColours[nextLayer]}")

    print(f"\n               Found : {len(runtime.MATERIALS.colours)} Colours")

    
def processFile(colourMatch, allowedDictionary, excludedColours, primitive_y_multiplier=1.0):
    """
    Process a single colour or sprite into an OBJ file, writing its 3D geometry.

    This function generates OBJ data row-by-row for the currently loaded image. It tracks
    colour usage, ensures consistent layer height, and applies optional bridging joints
    between diagonally adjacent pixels to strengthen print adhesion.

    Args:
        colourMatch (str): The hex code of the colour to process (or '' for all).
        allowedDictionary (dict): Colour keys to allow for inclusion.
        excludedColours (list): List of hex codes to exclude from processing.
        primitive_y_multiplier (float): Y scaling factor for vertical print depth.

    Returns:
        bool: True if file written successfully, False on error.

    Globals:
        pattern, pattern_w, pattern_h (image grid data)
        Image_MinX, Image_MaxX, Image_MinY, Image_MaxY (bounding box)
        MATERIALS.colours, MATERIALS.index (material data)
        Debug_Txt_File, WORKING_FILENAME, FILE_COUNTER (output state)
        Create_Towered_File, Create_Layered_File, ColoursOnSingleLayerHeight (mode flags)
        cube_vertices, cube_faces, cube_normals (OBJ geometry templates)
        joint_verticies, joint_faces, joint_normals (optional joint templates)
        CurrentZOffset, Primitive_Layer_Depth, Primitive_Initial_Layer_Depth (layering)

    TODO:
        - Break out inner row loop into reusable `processRow()` helper
        - Refactor joint-check logic into `applyDiagonalJointsIfNeeded()`
        - Use dataclass or config object for global state
        - Add verbose mode and structured logging
    """
 
    # Used to define the Current Face Counter
    # Needed to ensure Vertices are correctly defined.
    
    runtime.Current_Face = 0
    runtime.Current_Opposite_Face = 0

    thisColour = 1

    # Total Number of Primitives Created
    Total_Primitives = 0

    # Define RGB Colours as 0
    r, g, b, a = 0, 0, 0, 255



    # Define output Filenames based on Input, creating
    #   an  OBJ file with 3D Mesh Details
    #       TXT file with pixel data as seen

    TowerMultiplier = 1.0
    LastTowerMultiplier = 1.0

    if runtime.Create_Layered_File:
        obj_file = os.path.join(runtime.PATTERNS, "{}_Y{}{}.obj".format(runtime.WORKING_FILENAME,runtime.FILE_COUNTER,str(colourMatch)))
    else:
        obj_file = os.path.join(runtime.PATTERNS, "{}_Y{}.obj".format(runtime.WORKING_FILENAME,runtime.FILE_COUNTER))

    if runtime.Debug_Txt_File:
        txt_file = os.path.join(runtime.PATTERNS, "{}_Y{}{}.txt".format(runtime.WORKING_FILENAME,runtime.FILE_COUNTER,str(colourMatch)))

    # If we're adding Jointer Blocks this will be required.
    LastRow = False

    # open files for Writing, Note we're not checking their presence as we're overwriting/creating
    #   from scratch each time.
    try:
        if runtime.Debug_Txt_File:
           fp_txt=open(txt_file,'w')
           runtime.log(f"Creating Debug File: {txt_file}")
    except Exception as error:
        print(f"Failed to Create Debug file: {txt_file}\n")
        sys.exit(1)

    try:
        # TODO: Add some error checking here, rather than relay on TRY/CATCH Scenarios.
        with open(obj_file,'w') as fp_obj:
            runtime.log(f"Creating Object File: {obj_file}")
                # Create Header for OBJ File
            header = (
                "# Created using PNG2OBJ.py - © Jason Brooks 2022-2025\n"
                f"# Generated on: {datetime.now()}\n"
                f"# Original File: {runtime.WORKING_FILENAME}.png, Width: {runtime.IMAGE.width}, Height: {runtime.IMAGE.height}\n"
                "# License: MIT-NC (Non-Commercial use only, attribution required)\n"
                "# https://github.com/muckypaws/PNG2OBJ\n"
            )

            fp_obj.write( header )

            # Set Current Y Position, we're only using this for situations where sprite files
            #   make it difficult to seperate the blocks post conversion, so we add a space
            #   between the primitives on the 3D OBJ File
            start_y = 0

            # Work our way through each row of the PNG File.
            #for y in range(pattern_h):
            for y in range(runtime.IMAGE.min_y, runtime.IMAGE.max_y + 1):
                row = runtime.IMAGE.pattern[int(y % runtime.IMAGE.height)]
                
                # Get Next Row for Jointer Block Processing.
                # We're cheating by MOD by the PNG Height
                # But will set the Last row flag so we don't 
                # Process the rules for this. 
                nextRow = runtime.IMAGE.pattern[int((y+1) % runtime.IMAGE.height)]

                if runtime.Debug_Txt_File:
                    fp_txt.write('\n')

                # Check If We're processing the last row of Pixels
                if y == (runtime.IMAGE.height-1):
                    LastRow = True

                # If we're splitting models based on pixel width and height add and extra line
                #   And ensure we start the next primitive further down to enforce a gap in the model
                if y >0 and not(y % runtime.Pixel_H):
                    start_y = start_y + 1
                    if runtime.Debug_Txt_File:
                        fp_txt.write('\n')
                
                # Iterate through the data with
                start_x = 0
                pixel_found = False
                pixel_found_colour_index = 0
                primitive_width = 0
                primitive_x = 0
                runtime.lastPixelFound = -1
                LastTowerMultiplier = 1.0
                TowerMultiplier = 1.0

                #for x in range(pattern_w):
                for x in range(runtime.IMAGE.min_x,runtime.IMAGE.max_x + 1):
                    # Check if We're Adding extra space between each sprite based
                    #   on fixed pixel width per sprite.
                    if x > 0 and not(x % runtime.Pixel_W):
                        if runtime.Debug_Txt_File:
                            fp_txt.write("|")

                        # Close off this sprite.
                        if pixel_found:
                            thisColour = pixel_found_colour_index
                            if runtime.Create_Layered_File:
                                thisColour = list(runtime.MATERIALS.colours).index(colourMatch)
                            pixel_found = False
                            fp_obj.write( create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, cube_normals, False, thisColour, primitive_y_multiplier * TowerMultiplier) )
                            Total_Primitives += 1
                        # Reset Start Position of next Sprite
                        start_x=start_x+1
                        primitive_width = 0
                        primitive_x = start_x
                        runtime.lastPixelFound = -1

                    # Get Pixel from Row
                    pixel,mi, mm = getPixelFromRow(x, row, runtime.IMAGE.channels, runtime.IMAGE.width)

                    if runtime.Create_Towered_File:
                        LastTowerMultiplier = TowerMultiplier
                        if mm in allowedDictionary:
                            TowerMultiplier = list(allowedDictionary.keys()).index(mm) + 1.0
                        else:
                            TowerMultiplier = 0.01


                    # If Pixel present then add to TXT File and create primitive.
                    # if pixel > 0 and mi==colourIndex:
                    # if mi==colourIndex:
                    #if mm in allowedDictionary:

                    if checkProcessingRules(allowedDictionary, mm, excludedColours, pixel):
                        if runtime.Debug_Txt_File:
                            fp_txt.write("*")

                        if not pixel_found:
                            pixel_found = True
                            primitive_x = start_x
                            pixel_found_colour_index = mi
                        else:
                            # Check we're on the same colour
                            if mi != pixel_found_colour_index:
                            #if mm not in allowedDictionary:
                                if not checkNextPixelProcessingRules(allowedDictionary, mm):
                                    thisColour = pixel_found_colour_index
                                    if runtime.Create_Layered_File:
                                        thisColour = list(runtime.MATERIALS.colours).index(colourMatch)
                                    #fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False , pixel_found_colour_index) )
                                    #fp_obj.write( create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False , thisColour, primitive_y_multiplier, Primitive_Multiplier_Layers) )
                                    fp_obj.write( create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, cube_normals, False , thisColour, primitive_y_multiplier * LastTowerMultiplier))
                                    primitive_width = 0
                                    Total_Primitives += 1
                                    pixel_found_colour_index = mi
                                    primitive_x = start_x

                        # Update Primitive Width
                        primitive_width = primitive_width + 1

                    else:

                        if pixel_found:
                            thisColour = pixel_found_colour_index
                            if runtime.Create_Layered_File:
                                thisColour = list(runtime.MATERIALS.colours).index(colourMatch)
                            #fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False , pixel_found_colour_index) )
                            fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, cube_normals, False , thisColour, primitive_y_multiplier * LastTowerMultiplier) )
                            pixel_found = False
                            primitive_width = 0
                            Total_Primitives += 1

                        if runtime.Debug_Txt_File:
                            fp_txt.write(" ")

                    # Check if we're to add Jointer Blocks
                    if runtime.JOINTS_REQUIRED and not LastRow:
                        # Check if Blocks meet the Jointer rule
                        newJoint = CheckJointRequired(x, y, row, nextRow, runtime.IMAGE.channels, runtime.IMAGE.width)

                        if newJoint:
                            fp_obj.write(  create_primitive(start_x, start_y + 1, 1, 1, joint_verticies, joint_faces, joint_normals, newJoint, thisColour, primitive_y_multiplier * LastTowerMultiplier) )
                            newJoint = False



                    # Update X Position (Taking into account an offset if we're adding space between sprites)
                    start_x = start_x + 1

                # Update to the next Y Postion and check if we have an unwritten primitive to complete
                if pixel_found:
                    thisColour = pixel_found_colour_index
                    if runtime.Create_Layered_File:
                        thisColour = list(runtime.MATERIALS.colours).index(colourMatch)
                    fp_obj.write( create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, cube_normals, False, thisColour, primitive_y_multiplier * TowerMultiplier) )
                    pixel_found = False
                    primitive_width = 0
                    primitive_x = 0
                    Total_Primitives += 1

                start_y = start_y + 1

            # Write and Flush the Object File
            if primitive_width > 0:
                
                fp_obj.write(  create_primitive(start_x, start_y, primitive_width, 1, cube_vertices, cube_faces, cube_normals, False , 0, primitive_y_multiplier * TowerMultiplier) )

            fp_obj.write(f"#\n# Total Primitives Created: {Total_Primitives}\n#\n")

            runtime.log(f"Successfully Created Object File: {obj_file}\n")

    except Exception as error:
    # Bad Practice I know...
       print(f"Failed to write file: {obj_file}",obj_file)
       print(f"Exception: {error}")
       return False
    

    # Update Current Offset with multiplier requested

    if not runtime.ColoursOnSingleLayerHeight:
        #CurrentZOffset += (abs(Primitive_Multipler*primitive_y_multiplier*CUBE_Y)) # Shift Vertices Up a Layer...
        runtime.CurrentZOffset += runtime.Primitive_Layer_Depth * runtime.Primitive_Multiplier_Layers

        # Bit of a bodge, but set the next layer height depth going forward.
        if runtime.Primitive_Initial_Layer_Depth != 0.0:
            runtime.Primitive_Layer_Depth = runtime.Primitive_Initial_Layer_Depth
            runtime.Primitive_Initial_Layer_Depth = 0.0

    # Write and Flush the TXT File
    if runtime.Debug_Txt_File:
        fp_txt.write('\n')
        fp_txt.flush()
        fp_txt.close()

    #if CREATE_MTL_FILE:
    #    FinaliseMasterMaterialFile(mtl_filename)
    return True

#
# Check Processing Rule to Create Objects
#
def checkProcessingRules(allowedColours, currentColour, excludedColours, pixel):
    """
    Determine if a pixel colour should be processed based on current filtering rules.

    This is used during image traversal to apply inclusion/exclusion logic
    for multi-layer or filtered rendering. It can enforce user-specified colour
    limits or prevent redundant layer output.

    Args:
        allowedColours (dict or list): Set of colours permitted for processing.
        currentColour (str): The current pixel's colour code (hex).
        excludedColours (list): Colour hex codes explicitly skipped.
        pixel (int): Pixel intensity index or count (-1 for invalid/transparent).

    Returns:
        bool: True if the colour should be processed, False otherwise.

    Globals:
        lastPixelFound (str): Stores the most recent valid pixel for layered mode.
        Create_Layered_File (bool): Mode flag indicating per-layer processing.

    TODO:
        - Consider using a structured config or state object
        - Consolidate logic with higher-level decision flow
        - Replace pixel < 0 check with named constant or utility
    """

    if pixel <0:
        return False
    
    if len(allowedColours) > 0:        
        if runtime.Create_Layered_File:
            if currentColour in allowedColours and currentColour not in excludedColours:
                runtime.lastPixelFound = currentColour
                return True
            return False

        #if lastPixelFound == currentColour:
        if currentColour in allowedColours:
            return True
    else:
        if currentColour not in excludedColours:
            return True

    return False

def checkNextPixelProcessingRules(allowedColours, currentColour):
    """
    Determine if the next pixel's colour should be processed under current layer rules.

    This function is typically called after a previous pixel has passed inclusion tests.
    It enforces consistency in layer colour when `Create_Layered_File` is enabled,
    and avoids repeated processing of the same colour if not intended.

    Args:
        allowedColours (list or dict): Set of colours currently permitted for processing.
        currentColour (str): Hex code of the colour being evaluated.

    Returns:
        bool: True if the pixel should be processed, False otherwise.

    Globals:
        lastPixelFound (str): Tracks the last processed colour layer.
        Create_Layered_File (bool): Determines if individual colour layers are used.

    TODO:
        - Make `lastPixelFound` tracking optional or per-instance
        - Clarify distinction between first-pass and next-pass validation
        - Refactor to a more descriptive function name (e.g., `isColourRepeatAllowed`)
    """

    if runtime.Create_Layered_File:
        if currentColour not in allowedColours:
            return False
        else:
            return True
    
    if currentColour != runtime.lastPixelFound:
        runtime.lastPixelFound = currentColour
        return False
    
    return True

#
# Write Cached Material Information to Material File if Required
#
def CreateMasterMaterialFileMaster(filename):
    """
    Write the full MTL (Material Library) file to disk containing all colours used.

    This function outputs all entries in `MATERIALS.materials` to a `.mtl` file with headers,
    attribution, and a count summary at the end. It includes error handling for file access
    issues and logs output status.

    Args:
        filename (str): Full path or filename for the output `.mtl` file.

    Returns:
        None. Writes file to disk and prints status messages.

    Globals:
        MATERIALS.materials (list[str]): All formatted material entries (MTL strings).
        DEBUG (bool): Enables detailed exception logging.

    TODO:
        - Add option to overwrite or append mode
        - Move header string to a centralised template
        - Support previewing colour summary as table or HTML
    """

    try:
        output_path = Path(filename).resolve()

        with output_path.open('w', encoding='utf-8') as fp_mtl:
            fp_mtl.write("# Created with PNG2ObjV3.PY (C) Jason Brooks\n")
            fp_mtl.write("# See www.muckypaws.com and www.muckypawslabs.com\n")
            fp_mtl.write("# https://github.com/muckypaws/PNG2OBJ\n\n")

            for _, line in enumerate(runtime.MATERIALS.materials):
                fp_mtl.write(f"{line}")

            fp_mtl.write(f"#\n# Total Material Colours Created: {len(runtime.MATERIALS.materials)}\n#\n")

        print(f"✅ Material file written: {output_path}")

    except PermissionError:
        print(f"❌ Cannot write to {filename} — file is locked or open in another application.")
    except Exception as error:
        print(f"❌ Failed to create Material File: {filename}")
        print(f"Error: {error}")
        if runtime.DEBUG:
            import sys
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
        sys.exit(1)

                    
#
# Default Logging Code
#

#
# Position the Vertex Data based on Current X, Y Position on Grid
# And Currently Scaling Factors
#
def PositionDesign(vertices,x,y):
    """
    Translate a list of vertex coordinates by X and Y multipliers based on cube size.

    Applies positional offsets to a list of 3D vertices, typically used to shift a cube
    or block instance into its correct location in the grid space.

    Args:
        vertices (list[list[float]]): A list of [x, y, z] vertex coordinates.
        x (int): Grid X-index for placement.
        y (int): Grid Y-index for placement.

    Returns:
        list[list[float]]: A new list of adjusted vertices.

    Globals:
        CUBE_X (float): Physical cube width (used for translation).
        CUBE_Y (float): Physical cube height (used for translation).

    TODO:
        - Accept cube size as parameter instead of relying on globals
        - Consider vector or numpy-based operations for performance
    """
    nextVertices = []
    for index, vertex in list(enumerate(vertices)):
        # Get vertices
        v1 = vertex[0] + (x * runtime.CUBE_X)
        v2 = vertex[1] + (y * runtime.CUBE_Y)
        v3 = vertex[2]

        nextVertices.append([v1, v2, v3])

    return nextVertices

#
# Rotate top of the cube, Pass
#       Simple Cube Vertice
#       X Position
#       Centre X Position
#       Centre Y Position
#       Radius Of Circle
#
def createDesign2(new_vertices,x,cx,cy,Radius):
    """
    Create a warped cube-like structure by manipulating its top vertices.

    along a circular arc to simulate a rotated trapezoidal prism.

    This is often used in wave-like optical distortion or parametric shaping.

    Args:
        new_vertices (list): List of 8 vertex coordinates (expected base cube).
        x (float): Horizontal offset from center for distortion calculation.
        cx (float): Center X position.
        cy (float): Center Y position.
        Radius (float): Radius of curvature for the top arc.

    Returns:
        list: List of 8 updated vertex positions with transformed top surface.

    TODO:
        - Make trapezoid height (`v3`) a parameter
        - Add fallback or raise Exception instead of `exit(0)`
        - Document visual transformation with diagram or inline visual preview
    """
    if len(new_vertices) != 8:
        print(f"Sorry Wrong Input Data: {new_vertices}")
        sys.exit(1)

    # First four Vertices are the base of the design
    nextVertices = []
    nextVertices.append(new_vertices[0])
    nextVertices.append(new_vertices[1])
    nextVertices.append(new_vertices[2])
    nextVertices.append(new_vertices[3])

    # Calculate rotation on X-Axis of Top of Cube by Setting X and Y

    v1 = x
    v2 = math.sqrt(Radius*Radius - x*x)
    v3 = 10                             # Depth of 10 

    # Set the tops accordingly (Top Left)
    nextVertices.append([cx+x, v2+cy, v3])

    # Set the tops accordingly (Bottom Left)
    nextVertices.append([cx-Radius+v1, cy+(Radius-v2),v3])

    # Set the tops accordingly (Top Right
    nextVertices.append([cx+Radius-v1, cy-(Radius-v2), v3])

    # Set the tops accordingly (Bottom Right)
    nextVertices.append([cx-v1,cy-v2, v3])

    return nextVertices


#
# Rotate top of the cube, Pass
#       Simple Cube Vertex Data
#       Angle = Rotation in Degrees
#       Centre X Position
#       Centre Y Position
#       Radius Of Box
#       Depth = Height of TrapezoidalPrism (Default 10.0)
#
def createDesignTrapezoidalPrismTopRotation(new_vertices, Angle, cx, cy, Radius, Depth=10.0):
    """
    Create a trapezoidal prism by rotating the top face around the Z-axis with circular projection.

    The function modifies the top four vertices of a cube to follow a rotational
    arc based on the specified angle and radius, producing a skewed or twisted
    top face — useful for simulating waveforms or parametric distortion.

    Args:
        new_vertices (list): List of 8 base vertex coordinates (expects a full cube).
        Angle (float): Rotation angle in degrees, used to define curvature.
        cx (float): X-center of rotation.
        cy (float): Y-center of rotation.
        Radius (float): Radius of curvature or arc circle.
        Depth (float, optional): Z-depth of extrusion. Defaults to 10.0.

    Returns:
        list: New list of 8 transformed vertex coordinates.

    TODO:
        - Raise a proper exception instead of `exit(0)` on malformed input
        - Consider generalising arc control (skew, taper, etc.)
        - Add input validation for angle, radius, and Depth
    """
    if len(new_vertices) != 8:
        print(f"Sorry Wrong Input Data: {new_vertices}")
        sys.exit(1)

    # First four Vertices are the base of the design
    nextVertices = []
    nextVertices.append(new_vertices[0])
    nextVertices.append(new_vertices[1])
    nextVertices.append(new_vertices[2])
    nextVertices.append(new_vertices[3])

    if Angle >= 90.0:
        Angle = Angle - 90.0
    if Angle <= -90.0:
        Angle = Angle + 90.0
    


    # Calculate rotation on X-Axis of Top of Cube by Setting X and Y

    v1 = (Radius * math.cos(math.radians(Angle-45.0)))
    v2 = (Radius * math.sin(math.radians(Angle-45.0)))

    # Set the tops accordingly (Top Left)
    nextVertices.append([cx-v1, cy+v2, Depth])

    # Set the tops accordingly (Bottom Left)
    nextVertices.append([cx-v2, cy-v1, Depth])

    # Set the tops accordingly (Top Right
    nextVertices.append([cx+v2, cy+v1 , Depth])

    # Set the tops accordingly (Bottom Right)
    nextVertices.append([cx+v1, cy-v2, Depth])

    return nextVertices

#
# Apply Sine Wave to Z Axis
#
def ApplySineWaveToVertices(interimDesign, Amplitude, divisor=40.0, offsetX = 0.0, offsetY = 0.0):
    """
    Apply a sine-based parametric surface warp to the Z-coordinates of vertices.

    This function creates a distorted, wave-like surface by adjusting Z-values
    using a sinusoidal function based on X/Y position. Typically used for dynamic
    surface shaping in illusion or audio-reactive print designs.

    Args:
        interimDesign (list): List of 8 vertex coordinates from a base or modified cube.
        Amplitude (float): Strength of the sine deformation.
        divisor (float): Scaling factor for spatial frequency of the sine wave.
        offsetX (float): Positional offset applied to X-axis for wave shaping.
        offsetY (float): Positional offset applied to Y-axis for wave shaping.

    Returns:
        list: Transformed list of vertex coordinates with adjusted Z-values.

    Notes:
        - Vertices with Z=0.0 are considered base-level and left untouched.
        - Output ensures non-zero volume by forcing minimum Z of 0.1 when deformation is too shallow.

    TODO:
        - Replace `exit(0)` with exception
        - Allow waveform type selection (sine, square, triangle, etc.)
        - Accept custom phase offset or wave center
    """
    if len(interimDesign) < 4:
        print(f"Sorry Wrong Input Data: {interimDesign}")
        sys.exit(1)

    # First four Vertices are the base of the design
    nextVertices = []

    # Calculate Z Sinewave

    for index, vertices in enumerate(interimDesign):
        if vertices[2] == 0.0:
            nextVertices.append(vertices)
        else:
            # Parametric Equation Z = sqrt(sin(X^2 + Y^2)) * Amplitude
            newz = -math.sin(math.sqrt(((vertices[0]+offsetX)**2)/divisor + ((vertices[1]+offsetY)**2)/divisor)) * Amplitude

            # Ensure bottom always Zero
            if newz + vertices[2]<=0.0:
                # Ensure there's some volume to a face...
                nextVertices.append([vertices[0], vertices[1], 0.1])
            else:
                nextVertices.append([vertices[0], vertices[1], vertices[2]+newz])

    return nextVertices

#
# Apply Hemisphere Wave to Z Axis
#
def ApplyHemiSphereToVertices(interimDesign, Radius, divisor=40.0, offsetX = 0.0, offsetY = 0.0, offsetZ = 0.0):
    """
    Apply a hemispherical surface deformation to the upper vertices of a 3D shape.

    For each vertex with Z > 0.0, this function checks if it lies within a given radius
    from a center point and adjusts its Z-height based on the geometry of a hemisphere.
    Useful for creating dome-like distortions or bulges in parametric designs.

    Args:
        interimDesign (list[list[float]]): List of 3D vertex coordinates.
        Radius (float): Radius of the hemisphere to project within.
        divisor (float): Unused in current version (reserved for possible scaling).
        offsetX (float): Horizontal offset of hemisphere center.
        offsetY (float): Vertical offset of hemisphere center.
        offsetZ (float): Additional vertical displacement applied to curved vertices.

    Returns:
        list[list[float]]: Modified list of vertices with hemisphere Z-adjustment applied.

    TODO:
        - Replace sys.exit(0) with exception handling
        - Allow full sphere deformation for 360° wrapping
        - Add preview mode for visual verification
        - Remove unused `divisor` or apply for curve falloff
    """
    if len(interimDesign) < 4:
        print(f"Sorry Wrong Input Data: {interimDesign}")
        sys.exit(1)

    nextVertices = []

    for index, vertices in enumerate(interimDesign):
        # If Z = 0.0 then base vertices just copy
        # if index < (len(interimDesign)/2):
        if vertices[2] <= 0.0:
            nextVertices.append([vertices[0], vertices[1], 0.0])
        else:
            # Process Upper Hemisphere - Are we in radius of the Sphere?
            mylen = math.sqrt(((vertices[0]-offsetX)**2) + ((vertices[1]-offsetY)**2))
            
            if mylen <= Radius:
            # r^2 = (x-a)^2 + (y-b)^2 + (z-c)^2
            # Therefore Z = SQRT(r^2 - (x-a)^2 + (y-b)^2)
            # Where A, B, C = Offset of Sphere.  We're only interested in the Hemisphere.
                x2 = (vertices[0]-offsetX)**2
                y2 = (vertices[1]-offsetY)**2
                r2 = Radius ** 2
                z2 = abs(r2 - x2 - y2)

                #newz = (math.sqrt( ((vertices[0]-offsetX)**2)/divisor + (((vertices[1]-offsetY)**2)/divisor)))
                newz = math.sqrt(z2) + offsetZ

                if newz > 0.0:
                    nextVertices.append([vertices[0], vertices[1], newz])
                else:
                    nextVertices.append(vertices)
            else:
                nextVertices.append(vertices)

    return nextVertices

#
# Change the Colours of the Parametric Object to that of a PNG image... 
#
def ApplyPNGColoursToParametricObjects(vertDict, offsetX, offsetY, allowedDictionary, excludedColours):
    """
    Apply material indices to a vertex dictionary based on corresponding pixel colours in a PNG.

    This function overlays the pixel grid from a loaded PNG onto a dictionary of
    3D geometry positions and injects the correct material index (`mi`) into each
    corresponding vertex entry based on colour filtering logic.

    Args:
        vertDict (dict): Dictionary of vertex keys (e.g. "0023:0041") mapped to vertex data arrays.
        offsetX (int): Horizontal offset applied to the pixel lookup.
        offsetY (int): Vertical offset applied to the pixel lookup.
        allowedDictionary (dict): Dictionary of colours to include.
        excludedColours (list): Colours to skip.

    Returns:
        None. Modifies vertDict in-place by updating the colour/material index in entry [3].

    Globals:
        pattern, pattern_h, pattern_w (image data)
        channels (int): Number of colour channels in the PNG.
        Image_MinX, Image_MaxX, Image_MinY, Image_MaxY: Bounding box.
        Pixel_W, Pixel_H: Used for sprite sheet separation logic.

    TODO:
        - Refactor to support parametric key generators
        - Replace `print` placeholder with meaningful logging
        - Consider modularising sprite-spacing logic
    """
    start_y = offsetY
    for y in range(runtime.IMAGE.min_y, runtime.IMAGE.max_y + 1):
        row = runtime.IMAGE.pattern[int(y % runtime.IMAGE.height)]

        # If we're splitting models based on pixel width and height add and extra line
        #   And ensure we start the next primitive further down to enforce a gap in the model
        if y >0 and not(y % runtime.Pixel_H):
            start_y = start_y + 1
        
        # Iterate through the data with
        start_x = offsetX


        for x in range(runtime.IMAGE.min_x,runtime.IMAGE.max_x + 1):
            # Check if We're Adding extra space between each sprite based
            #   on fixed pixel width per sprite.
            if x > 0 and not(x % runtime.Pixel_W):
                start_x += 1

            # Get Pixel from Row
            pixel,mi, mm = getPixelFromRow(x, row, runtime.IMAGE.channels, runtime.IMAGE.width)

            if checkProcessingRules(allowedDictionary, mm, excludedColours, pixel):
                myKey = f"{(x+offsetX):04d}:{(y+offsetY):04d}"
                if myKey in vertDict:
                    VertexData = vertDict[myKey]
                    vertDict[myKey] = [VertexData[0], VertexData[1], VertexData[2] , mi]

            # Update X Position (Taking into account an offset if we're adding space between sprites)
            start_x = start_x + 1

        start_y = start_y + 1
#
#
#
def CreateOBJFileFromDictionary(filename, vertDict, primitive_y_multiplier, LastTowerMultiplier):
    """
    Write a complete `.obj` file from a dictionary of vertex primitives.

    This function iterates over a dictionary of vertex data keyed by position,
    formats each into an OBJ-formatted string using `create_primitive()`, and writes
    the result to an output file. It also adds a header including creator info and source image.

    Args:
        Filename (str): Base filename (without extension) for the output OBJ.
        vertDict (dict): Dictionary of pixel keys (x:y) to lists of [verts, faces, normals, colour_index].
        primitive_y_multiplier (float): Multiplier for depth scaling of primitives.
        LastTowerMultiplier (float): Tower height multiplier for layered mode.

    Returns:
        bool: True on success, False on write error.

    Globals:
        Create_Layered_File (bool): Affects filename output structure.
        PATTERNS (str): Output folder path.
        FILE_COUNTER (int): Index to distinguish multiple outputs.
        colourMatch (str): Name of current colour layer (used in layered mode).
        WORKING_FILENAME (str): Name of input file for header.
        pattern_w (int): Width of source PNG.
        pattern_h (int): Height of source PNG.

    TODO:
        - Add proper file existence checks before writing
        - Improve filename handling to avoid global pollution
        - Separate header formatting into its own reusable helper
    """
    try:
        if runtime.Create_Layered_File:
            obj_file = Path(runtime.PATTERNS) / f"{filename}_Y{runtime.FILE_COUNTER}{colourMatch}.obj"
        else:
            obj_file = Path(runtime.PATTERNS) / f"{filename}_Y{runtime.FILE_COUNTER}.obj"

        obj_file = obj_file.resolve()

        with obj_file.open("w", encoding="utf-8") as fp_obj:
            header = (
                "# Creator PNG2OBJ.py - © Jason Brooks 2022\n"
                f"# {datetime.now()}\n"
                f"# Original File: {runtime.WORKING_FILENAME}.png, Width: {runtime.IMAGE.width}, Height: {runtime.IMAGE.height}\n"
            )
            fp_obj.write(header)

            for key, value in vertDict.items():
                x, y = map(int, key.split(":"))
                colourIndex = value[3]
                fp_obj.write(
                    create_primitive(
                        x, y, 1, 1,
                        value[0], value[1], value[2],
                        False, colourIndex,
                        primitive_y_multiplier * LastTowerMultiplier,
                        False
                    )
                )

        print(f"✅ OBJ file written: {obj_file}")
        return True

    except PermissionError:
        print(f"❌ Cannot write to OBJ file — it may be open or locked: {obj_file}")
    except Exception as error:
        print(f"❌ Failed to write OBJ file: {obj_file}")
        print(f"Error: {error}")
        if runtime.DEBUG:
            import sys
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
    return False

#
# Add default Materials to MTL File
#
def addDefaultMaterialColours():
    """
    Preload the most common RGB primary and secondary colours into the material dictionary.

    This is used to ensure that basic colours are always available in MTL output even
    if not found directly in the loaded PNG image.

    Colours added:
        - Black
        - Red
        - Green
        - Blue
        - Yellow
        - Purple
        - Cyan
        - White

    Returns:
        None. Updates the global material list via `MATERIALS.register()`.

    TODO:
        - Parameterise the palette or load from external config
        - Extend to include greyscale and tertiary tones
        - Add option to tag with use context (e.g., outline, highlight)
    """
    # Black
    runtime.MATERIALS.register(0,0,0,0)
    # Red
    runtime.MATERIALS.register(255,0,0,0)
    # Green
    runtime.MATERIALS.register(0,255,0,0)
    # Blue
    runtime.MATERIALS.register(0,0,255,0)
    # Yellow
    runtime.MATERIALS.register(255,255,0,0)
    # Purple
    runtime.MATERIALS.register(255,0,255,0)
    # Cyan
    runtime.MATERIALS.register(0,255,255,0)
    # White
    runtime.MATERIALS.register(255,255,255,0)

#
# Can we create a simple parametric set of shapes?
#
def ParametricTest(Filename):
    """
    Generate a parametric test grid using custom-shaped 3D primitives and apply multiple.

    waveform-based surface distortions, then write the result to an OBJ file.

    This function creates a tiled grid of trapezoidal prisms, applies sine wave
    and hemispherical deformations to their Z surfaces, and optionally colours them
    based on a loaded PNG overlay using spatial key matching.

    Args:
        Filename (str): Output file name for the final OBJ.

    Returns:
        None. Writes OBJ and MTL files to disk.

    Globals:
        cube_normals (list): Normal data reused across all primitives.
        MATERIALS.process_only (list): List of colours allowed for processing.
        MATERIALS.exclusion (list): Colours to be skipped from processing.
        mtl_filename (str): Base filename used for the MTL output.
        Primitive_Layer_Depth (float): Extrusion Z depth of each cube.
        Primitive_Multipler (float): Scaling applied to cube dimensions.
        fp_obj (file-like, optional): May be used in live preview version (commented).
    
    TODO:
        - Externalise wave parameters into config or CLI input
        - Refactor into separate generator and transformer phases
        - Add preview/export toggle for colour overlay pass
        - Clean up old commented code paths for rotation variants
    """

    LastTowerMultiplier = 1.0
    primitive_y_multiplier = 1.0
    runtime.Primitive_Layer_Depth = 10.0
    runtime.Primitive_Multipler = 1.0

    # Test mod primitive
    new_vertices = ([ 0.000000,  0.000000, 0.000000],
                    [ 0.000000, 10.000000, 0.000000],
                    [10.000000,  0.000000, 0.000000],
                    [10.000000, 10.000000, 0.000000],

                    [0.000000, 10.000000, 25.000000],
                    [0.000000, 0.000000, 25.000000],
                    [10.000000, 10.000000, 25.000000],
                    [10.000000, 0.000000, 25.000000]
)
    new_faces = ([2, 4, 3, 1],
                [6, 8, 7, 5],
                [1, 3, 8, 6],
                [1, 6, 5, 2],
                [5, 7, 4, 2],
                [4, 7, 8, 3])

    VerticesDict = {}

    xRange = 9
    yRange = 9

    Radius = 5.0
    xSteps = Radius/5.0

    alternate = False

    startstep = 0.0
    currentAngle = 0.0
    angleSteps = 90.0 / 40.0

    waveSteps = 180.0 / 20.0

    VerticesDict = {}

    OffsetX = 5.0
    OffsetY = 5.0

    GridWidth = 30
    GridHeight = 20

    colourIndex = 2

    for y in range (-GridHeight,GridHeight):
        xPos = 0
        startstep = ((float(y) * xSteps)/20) % Radius
        angleStep = float(y) * angleSteps
        waveStart = waveSteps * float(y)

        for x in range (-GridWidth,GridWidth):

            #myDesign = createDesign(new_vertices,x,y)

            currentStep = float(x) * xSteps
            #myDesign = createDesign2(new_vertices,((currentStep+startstep) % float(Radius))  ,5.0,5.0,Radius)

            vx = (float(x)*10.0) - OffsetX
            vy = (float(y)*10.0) - OffsetY

            rotationAngle = -(math.degrees(math.atan2(-vy,vx)))

            #myDesign = createDesignTrapezoidalPrismTopRotation(new_vertices,(((float(x)*angleSteps)-45+angleStep) % 90.0)  ,-2,-10.0,Radius, 25.0)
            #myDesign = createDesignTrapezoidalPrismTopRotation(new_vertices,rotationAngle ,-3,15,Radius, 25.0)
            myDesign = createDesignTrapezoidalPrismTopRotation(new_vertices,0.0 ,5.0,5.0,5.0, 25.0)
            
            #interimDesign = PositionDesign(myDesign,x,y)
            interimDesign = PositionDesign(new_vertices,x,y)
            
            
            interimDesign = ApplySineWaveToVertices(interimDesign, 22, 200.0, -100.0)
            interimDesign = ApplySineWaveToVertices(interimDesign, 40, 175.0,-50.0,75.0)
            nextDesign = ApplyHemiSphereToVertices(interimDesign, 300.0,1.0, 50.0,-60,-250)

            if alternate:
                if y % 2:
                    if x % 2:
                        print("*", end="")
                        fp_obj.write( create_primitive(x, y, 1, 1, nextDesign, new_faces, cube_normals, False , 1, primitive_y_multiplier * LastTowerMultiplier, False))
                                
                    else:
                        print(" ",end="")
                else:
                    if not x % 2:
                        print("*", end="")
                        fp_obj.write( create_primitive(x, y, 1, 1, nextDesign, new_faces, cube_normals, False , 1, primitive_y_multiplier * LastTowerMultiplier, False))
                        
                    else:
                        print(" ",end="")
                print("")
            else:
                key = f"{x:04d}:{y:04d}"
                VerticesDict[key] = [nextDesign, new_faces, cube_normals, colourIndex]
                #fp_obj.write( create_primitive(x, y, 1, 1, nextDesign, new_faces, cube_normals, False , 1, primitive_y_multiplier * LastTowerMultiplier, False))

    # Apply PNG Process
    #ApplyPNGColoursToParametricObjects(VerticesDict,-2,-2, MATERIALS.process_only, MATERIALS.exclusion)
    ApplyPNGColoursToParametricObjects(VerticesDict, 0, 0, runtime.MATERIALS.process_only, runtime.MATERIALS.exclusion)

    CreateOBJFileFromDictionary(Filename, VerticesDict, primitive_y_multiplier, LastTowerMultiplier)
    CreateMasterMaterialFileMaster(runtime.mtl_filename)

#
# Process SVG Options
#
def process_SVG_File(args):
    """
    Display selected runtime arguments, configure SVG rendering mode, and generate SVG output.

    This function is responsible for:
    - Displaying key user-selected parameters (for debugging and confirmation)
    - Routing to the appropriate SVG output mode (illusion, frame, or pixel block)
    - Performing canvas size calculations and layout decision logic
    - Writing the final SVG file and optionally opening it post-generation

    Args:
        args (Namespace): Parsed command-line arguments passed from main().

    Responsibilities:
        - Logs current configuration to stdout for verification.
        - Selects between:
            - `create_svg_frame400()` for 400mm frame layout
            - `create_svg()` for optical illusion mode
            - `create_svg_from_PNG()` for basic pixel-to-SVG conversion
        - Tracks and prints pixel, grid, light/dark tile statistics.
        - Calls `svg_savefile()` and optionally opens the file on the system.

    Returns:
        None. Outputs SVG to disk and may open it in the default viewer.

    Globals:
        Image_Real_Width / Height (int): Used for layout calculations.
        SVG.illusion_type_circle (bool): Switch between diagonal or circular illusion rendering.
        SVG.png_pixel_count (int): Foreground pixel tile count.
        SVG.grid_count (int): Total tile count (optional).
        SVG.light_count / SVG.dark_count (int): Light/dark tile metrics.
        DEBUG (bool): Enables error trace reporting during file opening.

    TODO:
        - Split this into `describe_runtime_config()`, `select_svg_render_mode()`, and `finalise_output()`
        - Support output of runtime parameters as JSON/LOG for automated batch tooling
        - Allow skipping visual preview with silent mode flag
    """

    if len(args.illusioncolourtable) == 4:
        runtime.SVG.illusion_colour_table = args.illusioncolourtable


    if args.colourset > -1:
        runtime.SVG.illusion_colour_table = SVG_COLOUR_SETS[args.colourset % len(SVG_COLOUR_SETS)]

    runtime.SVG.illusion_max_streak = args.maxstreak if args.maxstreak > 0 else runtime.SVG.illusion_max_streak

    if len(args.outfilename[0]) > 0:
        outfilename = os.path.join("{}.svg".format(Path(''.join(args.outfilename)).with_suffix('')))
    else:
        outfilename = os.path.join("{}.svg".format(Path(''.join(args.filename)).with_suffix('')))
    
    args.svg_radius_percent_x = max(0.0, min(args.svg_radius_percent_x, 100.0))
    args.svg_radius_percent_y = max(0.0, min(args.svg_radius_percent_y, 100.0))

    print("              SVG Parameters : ")
    print("              ---------------\n")
    if args.frame400:
        print(f"   Building for Frame 400mm x 400mm Guide File")
    print(f"   SVG Pixel Width Requested : {args.svg_pixel_width}mm")
    print(f"  SVG Pixel Height Requested : {args.svg_pixel_height}mm")
    print(f"         SVG Corner Radius X : {args.svg_radius_percent_x}%")
    print(f"         SVG Corner Radius Y : {args.svg_radius_percent_y}%")
    print(f"              Add loaded PNG : {args.svgaddpng}")

    if args.usegridcolours:
        print(f"            Use Grid Colours : {args.usegridcolours}")
    else:
        print(f"        Use PNG Real Colours : {args.userealcolours}")

    if args.illusion:
        print(f"             Create Illusion : {args.illusion}")
        print(f"       Illusion Colour Table : {args.illusioncolourtable}")
        if not args.illusioncircle:
            print(f"               Illusion Type : Diagonals")
        else:
            print(f"               Illusion Type : Circular")
        print(f"     Maximum Illusion Streak : {runtime.SVG.illusion_max_streak}")
        print(f"   Minimum Border to Add PNG : {args.minimumborder}")
        print(f"          Minimum Grid Width : {args.minimumgridwidth}")
        print(f"         Minimum Grid Height : {args.minimumgridheight}")
        if args.colourset >= 0:
            print(f"        Colour Set Requested : {args.colourset % len(SVG_COLOUR_SETS)}")

    print(f"              Create Outline : {args.outlineOnly}")
    print(f"             Output Filename : {outfilename}")
    print(f"Open SVG File after creation : {args.svgopen}\n")

    runtime.SVG.illusion_type_circle = args.illusioncircle

    if args.frame400:
        # Create an SVG File for The Range Frames with 400mm internal size and 405mm external size.
        # Creates the grid of pieces with PNG Image pieces represented by circles
        # and adds the registration marks for cutting mountboard using a Maped Ruler and Cutter (60mm offsets)
        create_svg_frame400(args.outlineOnly, args.svgaddpng,
                            args.svg_radius_percent_x,
                            args.svg_radius_percent_y)

    elif args.illusion:
        # Create the Optical Illusion Images using two contrasting colours for the tiles
        # and two contrasting tiles for the PNG Image

        # Create the Optical Illusion, using
        #   Number of block horizontal, vertical
        #   Draw Outlines Only
        #   Use the Real Colours of the PNG Image
        #   Add the PNG to the SVG File (False if you just want to create the illusion without the image.)
        blocks_horizontal = max((args.minimumborder * 2) + runtime.IMAGE.real_width, args.minimumgridwidth)
        blocks_vertical = max((args.minimumborder * 2) + runtime.IMAGE.real_height, args.minimumgridheight)
        create_svg(blocks_horizontal, blocks_vertical,
                    args.outlineOnly,
                    not args.usegridcolours,
                    args.svgaddpng ,
                    0.0, 0.0,
                    args.svg_pixel_width, args.svg_pixel_height,
                    args.svg_radius_percent_x, args.svg_radius_percent_y)
    else:
        # Simply create an SVG Block File from a PNG no other features.
        print ("Creating SVG File from PNG: ")
        create_svg_from_PNG(args.outlineOnly, not args.usegridcolours,
                            args.svg_pixel_width,args.svg_pixel_height,
                            args.svg_radius_percent_x, args.svg_radius_percent_y)

    # Report the Stats
    print(f'     Total PNG Pixels : {runtime.SVG.png_pixel_count}')
    if runtime.SVG.grid_count:
        print(f'     Total Grid Count : {runtime.SVG.grid_count}')
        if runtime.SVG.png_pixel_count:
            print(f'  Total Grid less PNG : {runtime.SVG.grid_count - runtime.SVG.png_pixel_count}')
    if runtime.SVG.light_count:
        print(f'  Total Light Inserts : {runtime.SVG.light_count}')
    if runtime.SVG.dark_count:
        print(f'   Total Dark Inserts : {runtime.SVG.dark_count}')

    # Create the Final SVG File.

    svg_savefile(outfilename)

    # Open file automatically?
    if args.svgopen:
        try:
            svg_path = Path(outfilename).resolve()
            print(f"\nAttempting to open file: {svg_path}")

            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', str(svg_path)))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(svg_path)
            else:  # Linux variants
                subprocess.call(('xdg-open', str(svg_path)))
        except Exception as error:
            print(f"⚠️ Failed to open file: {outfilename}")
            print(f"Reason: {error}")
            if runtime.DEBUG:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)

#
# The actual start of Python Code.
#
if __name__ == "__main__":
    """
    Command-line entry point for PNG2OBJ.

    This block:
    - Defines all accepted arguments (3D, SVG, sprite, colour control)
    - Applies default logic and mode switches (towered, layered, flat, SVG)
    - Displays summarised runtime config to help users confirm setup
    - Dispatches to:
        - ParametricTest() (waveform mode)
        - process_SVG_File() (SVG generator)
        - main() (standard 3D OBJ modes)
    - Writes MTL file if required at end of processing

    TODO:
    - Break argument setup into a reusable function (e.g., `parse_arguments()`)
    - Move config initialisation to its own `init_runtime_state()` method
    - Refactor to allow this to be called programmatically (e.g., from GUI or REST API)
    """
    # Add user options to the code
    #parser = argparse.ArgumentParser(description="Convert PNG Images to OBJ or SVG - Jason Brooks",
    #                                 epilog='https://github.com/muckypaws/PNG2OBJ')
    parser = CaseInsensitiveArgumentParser(description="Convert PNG Images to OBJ or SVG - Jason Brooks",
                                     epilog='https://github.com/muckypaws/PNG2OBJ')
    parser.add_argument("-j","--joints", help="Create small joining blocks where cubes are only attached via their corners", action="store_true", default=False)
    parser.add_argument("-m","--mtl",help="Create a Material File with the OBJECT", action="store_true", default=False)
    parser.add_argument("-lc","--listColours",help="List the colours discovered and quantity of pixels",action="store_true")
    parser.add_argument("filename",help="Include the PNG File to convert without the PNG Extension, i.e. art.png just pass art")
    parser.add_argument("-el","--excludelist",nargs="*",type=str, default=[])
    parser.add_argument("-ac","--alphacutoff",help="Cutoff Value for Alpha Byte (0-255), anything equal or below will be treated as fully transparent, above will be treated as fully opaque",type=int,default=128)
    parser.add_argument("-db","--debug",help="Create a Debug Text File with Pixels identified",action="store_true", default=False)
    parser.add_argument("-s","--sort",help="Sort the colours in order of most colour to least",action="store_true", default=False)
    parser.add_argument("-rs","--reversesort",help="Reverse the order of colours to process with most first",action="store_true",default=False)
    parser.add_argument("-pc","--processcolours",help="Process this colour list only",nargs="*",type=str, default=[])
    parser.add_argument("-bgh","--backgroundheight",help="Height multiplier for the initial background.  Default = 1.0",type=float, default=1.0)
    parser.add_argument("-lm","--layermultiplier",help="The Layer Multiplier to use, default 1.0",type=float,default=1.0)
    parser.add_argument("-nl","--nextlayeronly",help="Process none background colours on next height only",action="store_true", default=False)
    parser.add_argument("-sw","--spriteWidth",help="Width of Fixed Sprites in Sprite Sheet",type=int,default=runtime.DEFAULT_PIXEL_WIDTH)
    parser.add_argument("-sh","--spriteHeight",help="Height of Fixed Sprites in a Sprite Sheet",type=int,default=runtime.DEFAULT_PIXEL_HEIGHT)
    parser.add_argument("-mw","--maxwidth",help="Maximum Width of OBJ in mm (Sets Multipliers)",type=float,default=0.0)
    parser.add_argument("-mh","--maxheight",help="Maximum Height of OBJ in mm (Sets Multipliers)",type=float,default=0.0)
    parser.add_argument("-md","--maxdepth",help="Maximum depth of OBJ in mm (Sets Multipliers)",type=float,default=0.0)
    parser.add_argument("-ild","--initialLayerDepth",help="First Layer depth of OBJ in mm (Affects Multipliers)",type=float,default=0.0)
    parser.add_argument("-nf","--noframe",help="Don't Generate a Bounding Frame",action="store_true", default=False)
    parser.add_argument("-sz","--startZ",help="Initial Z Height Starting Position",type=float,default=0.0)

    # First Mutually Excluded Group of Flags
    group=parser.add_mutually_exclusive_group()
    group.add_argument("-fl","--flat",help="Create a Single OBJ File with all colour information",action="store_true", default=True)
    group.add_argument("--layered",help="Create a Multi Layer Set of files for each colour code",action="store_true",default=False)
    group.add_argument("--tower",help="Create a single layer, different heights based on colour order",action="store_true",default=False)
    # Parametric Testing
    parser.add_argument("-pt","--parametricTest",help="Testing a new idea",action="store_true", default=False)
    # SVG Files
    group.add_argument("-svg","--svg",help="Create an SVG File",action="store_true",default=False)
  
    # Get arguments from the Command Line
    # Added SVG Support
    parser.add_argument("-svgpw","--svg_pixel_width",help="Width of each Pixel for SVG Creation",type=float,default=20.0)
    parser.add_argument("-svgph","--svg_pixel_height",help="Height of each Pixel for SVG Creation",type=float,default=20.0)
    parser.add_argument("-svgrpx","--svg_radius_percent_x",
                        help="Radius of the rounded corners X",
                        type=float,default=25.0)
    parser.add_argument("-svgrpy","--svg_radius_percent_y",help="Radius of the rounded corners X",type=float,default=25.0)
    
    parser.add_argument("-illusion","--illusion",help="Create an SVG File with an optical illusion",action="store_true",default=False)
    parser.add_argument("-f400","--frame400",help="Create an SVG File designed for Frames of 400mm internal",action="store_true",default=False)
  
    parser.add_argument("-outfile","--outfilename",help="Filename of the SVG File to Generate",nargs=1,type=str, default=[""])
    parser.add_argument("-outline","--outlineOnly",help="Draw Outline only ready for machining",action="store_true",default=False)
    parser.add_argument("-svgaddpng","--svgaddpng",help="Add loaded PNG to SVG Output",action="store_true",default=False)
    parser.add_argument("-svgopen",help="Open SVG File with Default Application",action="store_true",default=False)
    parser.add_argument("-ict","--illusioncolourtable",help="Colour Table for Optical Illusion",nargs=4,type=str, default=["#3F53FF","#020078","#D93C41","#781314"])
    parser.add_argument("-mb","--minimumborder", help="Minimum Border to add to PNG Image",type=int,default=0)
    parser.add_argument("-mgw","--minimumgridwidth", help="Minimum Border to add to PNG Image",type=int,default=4)
    parser.add_argument("-mgh","--minimumgridheight", help="Minimum Border to add to PNG Image",type=int,default=4)
    parser.add_argument("-ilc","--illusioncircle", help="Illusion type circle not diagonals",action="store_true",default=False)
    parser.add_argument("-cset","--colourset", help="Which Colour Set to Use for Illusion",type=int,default=-1)
    parser.add_argument("-stmax","--maxstreak", help="Set Maximum Colour Run Streak for Optical Illusion",type=int,default=-1)
    
    group2=parser.add_mutually_exclusive_group()
    group2.add_argument("-urc","--userealcolours", help="Use PNG Actual Colours?",action="store_true",default=True)
    group2.add_argument("-ugc","--usegridcolours", help="Use PNG Grid Colours?",action="store_true",default=False)

    # Paramteric Options
    parser.add_argument("-ptn","--parametricFilename",help="Filename of Parametric File to Generate",nargs=1,type=str, default=["ParamtericTestFile"])

    args=parser.parse_args()



    # Are we processing 3D or 2D?
    ThreeD = not args.svg

    # Added for Parametric Testing
    if args.parametricTest:
        # Add default colours before processing the PNG Image.
        addDefaultMaterialColours()

    # Check for Jointer Cubes required.
    runtime.JOINTS_REQUIRED = args.joints

    # Check if We're creating the Material File.

    runtime.CREATE_MTL_FILE = args.mtl

    runtime.Create_Layered_File = args.flat
    runtime.Create_Layered_File = args.layered
    runtime.Create_Towered_File = args.tower

    runtime.ALPHACUTOFF = args.alphacutoff

    runtime.Sort_Colours_Flag = args.sort

    runtime.Primitive_Multiplier_Background = args.backgroundheight
    runtime.Primitive_Multiplier_Layers = args.layermultiplier

    # Ensure we're sorting if only one of the sort flags provided.
    if args.reversesort:
        runtime.Sort_Colours_Flag = True
        runtime.Sort_Direction = True

    # Ensure the Working Filename Has No Extension.
    if len(args.outfilename[0]) > 0:
        runtime.WORKING_FILENAME = Path(args.outfilename[0]).with_suffix('')
    else:
        runtime.WORKING_FILENAME = Path(args.filename).with_suffix('')

    # Set Material Filename
    runtime.mtl_filename = os.path.join(runtime.PATTERNS, "{}.mtl".format(runtime.WORKING_FILENAME))


    # First Stage, Get Colours In Memory first and see if we have something
    # Attempt to Load the PNG to memory.
    if loadPNGToMemory(args.filename) == False:
        print(f"Unable to open file: {args.filename}.png")
        sys.exit(1)
    
    if runtime.IMAGE.real_height < 1 or runtime.IMAGE.real_width < 1:
        print(f"No Image Data to Process, Quitting...")
        sys.exit(1)

    # Remove Excluded Colours from Process Colours List
    # If user provides both in both tables, we'll force exclusion!
    totalColours = len(runtime.MATERIALS.colours)
    for excluded in runtime.MATERIALS.exclusion:
        if excluded in runtime.MATERIALS.colours:
            totalColours -= 1

    if args.excludelist and not args.listColours:
        print(f"Excluding the following colours: {args.excludelist}\n")
        runtime.MATERIALS.exclusion = args.excludelist

    if args.processcolours:
        print(f"Only Processing the following colours: {args.processcolours}")
        runtime.MATERIALS.process_only = args.processcolours

    runtime.Debug_Txt_File = args.debug

    runtime.Pixel_W = args.spriteWidth
    runtime.Pixel_H = args.spriteHeight

    widthMultiplier = 0.01
    heightMultiplier = 0.01

    runtime.ColoursOnSingleLayerHeight = args.nextlayeronly



    print("")
    print(f"    Image Information :")
    print("    -------------------\n")
    print(f"           Image File : {args.filename}")
    print(f"       PNG Image Size : {runtime.IMAGE.width}px (width), {runtime.IMAGE.height}px (height)")
    print(f"   Number of Channels : {runtime.IMAGE.channels}")
    print("")
    print(f"     Joints Requested : {runtime.JOINTS_REQUIRED}\n Create Material File : {runtime.CREATE_MTL_FILE}")
    print(f" Reverse Sort Colours : {runtime.Sort_Colours_Flag}")
    print(f"Create Flat File Only : {not runtime.Create_Layered_File}" )
    print(f"         Alpha Cutoff : {runtime.ALPHACUTOFF}")


    if runtime.Pixel_W != runtime.DEFAULT_PIXEL_WIDTH:
        print(f"   Sprite Sheet Width : {runtime.Pixel_W}")
    if runtime.Pixel_H != runtime.DEFAULT_PIXEL_HEIGHT:
        print(f"  Sprite Sheet Height : {runtime.Pixel_H}")

    # Process file parameters for 3D Waveform OBJ Format
    if not args.svg:
        if args.maxheight != 0.0 or args.maxwidth != 0.0:
            # Need to calculate the Multipliers...
            widthMultiplier = args.maxwidth / runtime.IMAGE.real_width
            heightMultiplier = args.maxheight / runtime.IMAGE.real_height

            if widthMultiplier == 0.0:
                widthMultiplier = heightMultiplier

            if heightMultiplier == 0.0:
                heightMultiplier = widthMultiplier

            runtime.Primitive_Multipler = min(widthMultiplier, heightMultiplier) / 10.0

        # Calculate Layer Depths.
        if args.maxdepth != 0.0:
            # Do we need a fixed First Layer Depth?

            if not runtime.Create_Layered_File:
                runtime.Primitive_Initial_Layer_Depth = args.maxdepth
                runtime.Primitive_Layer_Depth = runtime.Primitive_Initial_Layer_Depth
            else:
                # If we didn't pass an colours to process (So all except the exception list)
                if args.initialLayerDepth != 0.0 and totalColours > 0 and len(args.processcolours) == 0:
                    # How many colours are we processing?
                    # If more than one, set layer heights accordingly.
                    if totalColours > 1:
                        runtime.Primitive_Initial_Layer_Depth = (args.maxdepth - args.initialLayerDepth)/(len(runtime.MATERIALS.colours)-1)
                        runtime.Primitive_Layer_Depth = args.initialLayerDepth
                    else:
                        # Only one colour to process so has to be maximum height.
                        runtime.Primitive_Initial_Layer_Depth = args.maxdepth
                        runtime.Primitive_Layer_Depth = runtime.Primitive_Initial_Layer_Depth
                    runtime.CurrentZOffset = 0.0

                if args.initialLayerDepth != 0.0 and len(runtime.MATERIALS.process_only) > 1 and len(args.processcolours) > 0:
                    # Set height of initial layer depth
                    runtime.Primitive_Layer_Depth = args.initialLayerDepth
                    runtime.Primitive_Initial_Layer_Depth = (args.maxdepth - args.initialLayerDepth) / (len(runtime.MATERIALS.process_only) - 1)
                    #Primitive_Layer_Depth = Primitive_Initial_Layer_Depth
                    runtime.CurrentZOffset = 0.0
                else:
                    #if len(MATERIALS.process_only) > 0:
                    if runtime.Primitive_Layer_Depth == 0.0:
                        if len(runtime.MATERIALS.process_only):
                            runtime.Primitive_Layer_Depth = args.maxdepth / len(runtime.MATERIALS.process_only)
                        else:
                            runtime.Primitive_Layer_Depth = args.maxdepth / totalColours

        else:
            runtime.Primitive_Layer_Depth = abs(runtime.Primitive_Multipler*runtime.CUBE_Y)

        if args.startZ != 0.0:
            runtime.CurrentZOffset = args.startZ

        print(f"Background Multiplier : {runtime.Primitive_Multiplier_Background:.2f}")
        print(f"     Layer Multiplier : {runtime.Primitive_Multiplier_Layers:.2f}")
        print(f"       Object Start Z : {args.startZ:.2f}mm")
        print(f" Object Max Depth (Z) : {args.maxdepth:.2f}mm")
        if runtime.Primitive_Initial_Layer_Depth != 0.0:
            print(f"      First Layer Depth : {runtime.Primitive_Layer_Depth:.2f}mm")
            print(f"      Next Layer Depths : {runtime.Primitive_Initial_Layer_Depth:.2f}mm")

        else:
            print(f"     Each Layer Depth : {runtime.Primitive_Layer_Depth:.2f}mm")

        if len(runtime.MATERIALS.process_only) > 0:
            print(f"     Requested Layers : {len(runtime.MATERIALS.process_only)}")

        print(f"     Background Frame : {not args.noframe}")

        if runtime.ColoursOnSingleLayerHeight:
            print(f"\n **** Seperate Colours On Single Layer Selected ****")


    if runtime.IMAGE.width != runtime.IMAGE.real_width or runtime.IMAGE.height != runtime.IMAGE.real_height:
        print(f"\n   Actual Image Width : {runtime.IMAGE.real_width} Pixels")
        print(f"  Actual Image Height : {runtime.IMAGE.real_height} Pixels")
        print(f"        Image Start X : {runtime.IMAGE.min_x}")
        print(f"        Image Start Y : {runtime.IMAGE.min_y}")
        print(f"         Bounding Box : ({runtime.IMAGE.min_x},{runtime.IMAGE.min_y},{runtime.IMAGE.max_x},{runtime.IMAGE.max_y}) ")

    if ThreeD:
        print(f"\n  Pixel Width/Height : {widthMultiplier:.2f}mm x {heightMultiplier:.2f}mm")
    else:
        print("\n            Requested : ")
        print(f"   Pixel Width/Height : {args.svg_pixel_width:.2f}mm x {args.svg_pixel_height:.2f}mm")
        print(f"          Rect Radius : {args.svg_radius_percent_x:.2f}% x {args.svg_radius_percent_y:.2f}%")

    if runtime.Debug_Txt_File:
        print(f"\n      Debug Text File : {runtime.Debug_Txt_File}\n")

    if len(runtime.MATERIALS.exclusion) > 0:
        print(f"\nColour list to exclude: {runtime.MATERIALS.exclusion}")
    if len(runtime.MATERIALS.process_only) > 0:
        print(f"\n   Colours to process : {runtime.MATERIALS.process_only}")

    print("\n")

    # Note: -lc / --listColours prints the discovered-colour summary and then
    # continues to normal conversion (it is not an informational-only switch);
    # the OBJ/MTL/SVG output is still produced.
    if args.listColours:
        displayColourInformation()

    #
    # Finally process the PNG File.
    #
    if args.parametricTest:
        print("Testing....")
        ParametricTest(args.parametricFilename[0])
        exit(0)
    # Process new SVG Options.
    elif args.svg:
        process_SVG_File(args)
    else:
        main(args.noframe)

    # Create the Material File if required.
    # Changed code to reduce IO to disk
    # Write the Material File at the end
    if args.mtl and not args.listColours:
        CreateMasterMaterialFileMaster(runtime.mtl_filename)
