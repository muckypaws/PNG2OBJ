#!/usr/bin/env python3
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

# Application Defaults
DEBUG = False
# Default location for File
PATTERNS=""

DEFAULT_PIXEL_WIDTH  = 99999999
DEFAULT_PIXEL_HEIGHT = 99999999

# Set Pixel Width and Height if Sprites are fixed width within the sheet, otherwise 
# use a high number.
Pixel_W = DEFAULT_PIXEL_WIDTH
Pixel_H = DEFAULT_PIXEL_HEIGHT

# PNG Data for Image loaded
pattern = 0
pattern_w = 0
pattern_h = 0
pattern_meta = 0
channels = 0

CurrentZOffset = 0.0

# X is positive, Y is negative unless you want to flip the image.
# Leave these alone, my initial mistake carried over... represents the value of the
# Primitive Cube defined as a 10 x 10 x 10... You can change it but... well...
# you really don't want to... trust me...
# unless you fix my code to handle this properly
# so yeah... leave it alone :)
CUBE_X = 10
CUBE_Y = -10

# Define the Alpha Value as Cut Off For the Pixel
ALPHACUTOFF = 128

# Define TRUE if Printing, FALSE if anything else as not required
JOINTS_REQUIRED = False

# Define TRUE if a corresponding MTL File is to be created for Colour Cubes
CREATE_MTL_FILE = False

# Define the Working Filename
WORKING_FILENAME = ""

# define the File Counter
FILE_COUNTER = 0

# Used to define the Current Face Counter
# Needed to ensure Vertices are correctly defined.
Current_Face = 0
Current_Opposite_Face = 0

#
# The multiplier to use when creating the background object
#
Primitive_Multiplier_Background = 1.0

#
# The multiplier to use when creating the background object
#
Primitive_Multiplier_Layers = 1.0


#
# When processing colours, only on height above background object
#
ColoursOnSingleLayerHeight = False

# Basic Definition of cube with 8 Vertices (4 Sets of Co-Ords per face)

'''
cube_vertices = (   [ 0.000000 , 10.000000,  0.000000],
                    [ 10.000000, 10.000000, 10.000000],
                    [ 10.000000, 10.000000,  0.000000],
                    [ 10.000000,  0.000000,  0.000000],
                    [ 0.000000 ,  0.000000, 10.000000],
                    [ 0.000000 , 10.000000, 10.000000],
                    [ 10.000000,  0.000000, 10.000000],
                    [ 0.000000 ,  0.000000,  0.000000]
)

cube_normals = (    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000])

# Basic Definition of a Primitives connecting faces 

cube_faces = (  [ 6, 2, 1],
                [ 1, 2, 3],
                [ 2, 7, 3],
                [ 3, 7, 4],
                [ 7, 5, 4],
                [ 4, 5, 8],
                [ 5, 6, 8],
                [ 8, 6, 1],
                [ 2, 6, 7],
                [ 7, 6, 5],
                [ 1, 3, 8],
                [ 8, 3, 4]
              )
'''

# Fixed 15/8/2024
'''
cube_vertices = (   [ 0.000000,	 0.000000,  10.000000],
                    [10.000000,	 0.000000,  10.000000],
                    [10.000000,	 0.000000,   0.000000],
                    [ 0.000000,	 0.000000,   0.000000],

                    [10.000000,	 0.000000,  10.000000],
                    [10.000000,  10.000000, 10.000000],
                    [10.000000, 10.000000,	 0.000000],
                    [10.000000,	  0.000000,	 0.000000],

                    [10.000000,	10.000000, 10.000000],
                    [ 0.000000,	10.000000, 10.000000],
                    [ 0.000000,	10.000000,	 0.000000],
                    [10.000000,	10.000000,	 0.000000],

                    [ 0.000000,	10.000000, 10.000000],
                    [ 0.000000,	   0.000000,10.000000],
                    [ 0.000000,	   0.000000, 0.000000],
                    [ 0.000000,	 10.000000, 0.000000],

                    [10.000000,	 0.000000,  10.000000],
                    [ 0.000000,	 0.000000,  10.000000],
                    [ 0.000000, 10.000000, 10.000000],
                    [10.000000, 10.000000, 10.000000],

                    [ 0.000000, 10.000000,	 0.000000],
                    [ 0.000000,	 0.000000,	 0.000000],
                    [10.000000,	 0.000000,	 0.000000],
                    [10.000000, 10.000000,	 0.000000]
)

cube_normals = (    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  0.000000,  1.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  1.000000,  0.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [  0.000000, -1.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [ -1.000000,  0.000000,  0.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000,  1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000],
                    [  0.000000,  0.000000, -1.000000]
)

cube_faces = (  [ 1,  2,  4],
                [ 4,  2,  3],
                [ 5,  6,  8],
                [ 8,  6,  7],
                [ 9, 10, 12],
                [12, 10, 11],
                [13, 14, 16],
                [16, 14, 15],
                [17, 18, 20],
                [20, 18, 19],
                [22, 23, 21],
                [21, 23, 24]
)
'''

#
# This is optimal from a vertex point of view, and resolves the issue of "Non-Manifold Edge" Errors
# Observed in some slicer and 3D Software, however the surface normals result in "Missing edges"
# when being rendered.  As described in Section 14.2.2 Surface Normals of 3D Math Primer for
# Graphics and Game Develpoment (Fletcher Dunn and Ian Parberry) ISBN 1-55622-911-9
# wordware publishing Inc, https://gamemath.com now discontinued.
# Take a look here https://gamemath.com/book/intro.html the online version describes the issue
# https://gamemath.com/book/graphics.html 10.4.2 (Fig 10.14)
#
cube_vertices = (   [  0.000000,  0.000000, 10.000000],
                    [ 10.000000,  0.000000, 10.000000],
                    [ 10.000000,  0.000000,  0.000000],
                    [  0.000000,  0.000000,  0.000000],

                    [ 10.000000, 10.000000, 10.000000],
                    [ 10.000000, 10.000000,  0.000000],
                    [  0.000000, 10.000000, 10.000000],
                    [  0.000000, 10.000000,  0.000000]
)

cube_normals = ( [ -1.000000,  1.000000,  1.000000],
                    [  1.000000,  1.000000,  1.000000],
                    [  1.000000,  1.000000, -1.000000],
                    [ -1.000000,  1.000000, -1.000000],
                    [  1.000000, -1.000000,  1.000000],
                    [  1.000000, -1.000000, -1.000000],
                    [ -1.000000, -1.000000,  1.000000],
                    [ -1.000000, -1.000000, -1.000000]
)

cube_faces = (  [ 1, 2, 4],
                [ 4, 2, 3],     # Bottom Face
                [ 2, 5, 3],
                [ 3, 5, 6],     # Right Face
                [ 5, 7, 6],
                [ 6, 7, 8],     # Top Face
                [ 7, 1, 8],
                [ 8, 1, 4],     # Left Face
                [ 2, 1, 5],
                [ 5, 1, 7],     # Rear Face
                [ 4, 3, 8],
                [ 8, 3, 6]      # Front Face
)



# Basic Definition for a Jointer Cube Where Pixels are connected by Corners Only
# This is needed if there's no overlap on your printer and want to ensure a 
# a connection that should lift off the printer.


joint_verticies = ( [ -3.00000, -0.000000,  0.000000],
                    [ -3.00000, -0.000000, 10.000000],
                    [  0.000000, -0.000000,  0.000000],
                    [  0.000000, -0.000000, 10.000000],
                    [  0.000000,  3.00000, 10.000000],
                    [  0.000000,  3.00000,  0.000000],
                    [  3.00000, -0.000000,  0.000000],
                    [  0.000000, -3.00000,  0.000000],
                    [  0.000000, -3.00000, 10.000000],
                    [  3.00000, -0.000000, 10.000000])




joint_normals = (   [ -1.110721,  0.460076, -0.785398],
                    [ -1.110721,  0.460075,  0.785398],
                    [  0.000000, -0.000000, -3.141593],
                    [  0.000000,  0.000000,  3.141593],
                    [ -0.460075,  1.110720,  0.785398],
                    [ -0.460075,  1.110721, -0.785398],
                    [  1.110721, -0.460076, -0.785398],
                    [  0.460075, -1.110721, -0.785398],
                    [  0.460075, -1.110720,  0.785398],
                    [  1.110721, -0.460075,  0.785398])


joint_faces = ( [1, 2, 3],
                [3, 2, 4],
                [5, 6, 4],
                [4, 6, 3],
                [3, 6, 7],
                [1, 3, 8],
                [4, 2, 9],
                [5, 4, 10],
                [7, 10, 3],
                [3, 10, 4],
                [9, 8, 4],
                [4, 8, 3],
                [2, 1, 9],
                [9, 1, 8],
                [10, 7 , 5],
                [5, 7, 6])



# Define the default Parameters for each new Material
#   See: https://www.loc.gov/preservation/digital/formats/fdd/fdd000508.shtml
#
default_mtl_params =    "\nKs 0.000000 0.000000 0.000000\n" \
                        "Tf 0.000000 0.000000 0.000000\n" \
                        "illum 4 \n" \
                        "d 1.0 \n" \
                        "Ns 100 \n" \
                        "sharpness 100 \n" \
                        "Ni 1\n" 

#
# Define the Colour Material Dictionary
#
mtl_colour_dict   = {}
mtl_final_list = []
mtl_current_index = 0
mtl_filename = ""
mtl_lib_filename = ""

#
# Colour Exclusion List
#
Colour_Exclusion_List = []

#
# Colour Process List
#
Colour_Process_Only_list = []
#
# Colours Require Sorting?
#
Sort_Colours_Flag = False

#
# Which type of Object File to Create?
#
Create_Layered_File = False

#
# Direction to sort the colour list for processing
#   False = Low to High, True = High to Low...
#
Sort_Direction = False

#
# Last coloured Pixel Found
#
lastPixelFound = 0

#
# Debug TXT File Required?
#
Debug_Txt_File = False

#
# Actual Pixels Found Details.
#
Image_MinX = 0
Image_MaxX = 0
Image_MinY = 0
Image_MaxY = 0
#
# Actual Image Found when removing Transparent Pixels
#
Image_Real_Width = 0
Image_Real_Height = 0

# Object X/Y Multiplier
Primitive_Multipler = 0.1

# Object Z Multiplier for each layer
Primitive_Layer_Depth = 0.0

# If we need a specific Initial Layer, this will override.
Primitive_Initial_Layer_Depth = 0.0

# Create a Single Layered File with Object Heights Dependent on Colour Order
# provided in the Process Colour Order list
Create_Towered_File = False

# Needed for SVG File Creation.
SVG_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
    '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
    '<!--\n'
    '  Generated by PNG2OBJ.py - © Jason Brooks 2022-2025\n'
    '  License: MIT-NC (Non-Commercial use only, attribution required)\n'
    '  Source: https://github.com/muckypaws/PNG2OBJ\n'
    '  This file is generated for personal/hobbyist use only.\n'
    '-->\n'
)

# Contains SVG Data
SVG_DATA_LIST = []

# Illusion Array Data
SVG_ILLUSION_ARRAY = []

# Canvas Width/Height
SVG_CANVAS_WIDTH = 0.0
SVG_CANVAS_HEIGHT = 0.0

ILLUSION_MAX_STREAK = 3

SVG_PNG_PIXEL_COUNT = 0
SVG_GRID_COUNT = 0
SVG_OPTICAL_ILLUSION_COUNT = 0
SVG_LIGHT_COUNT = 0
SVG_DARK_COUNT = 0

# Table is Defined as colours for Light Block, Dark Block, Light Pixel, Dark Pixel index 0, 1, 2, 3
SVG_ILLUSION_COLOUR_TABLE = ["#3F53FF","#020078","#D93C41","#781314"]

# Some sample colour sets, feel free to amend/adjust as you desire
SVG_COLOUR_SETS = { 0:["#3F53FF", "#020078", "#D93C41", "#781314"],
                    1:["#FFF300", "#DD9C3D", "#394C93", "#000F45"],
                    2:["#F6C6CD", "#FF4862", "#00FF60", "#005506"],
                    3:["#D93C41", "#781314", "#00FF60", "#005506"],
                    4:["#3F53FF", "#020078", "#c0c0c0", "#676767"],
                    5:["#0092FF", "#6600FF", "#F82AB9", "#B70A2B"]
                   }

# Indexs into the colour table above.
LIGHT_BLOCK_INDEX = 0
DARK_BLOCK_INDEX = 1
LIGHT_PIXEL_INDEX = 2
DARK_PIXEL_INDEX = 3

# Create Circles instead of Diagonals?
ILLUSION_TYPE_CIRCLE = False


# Custom ArgumentParser to make option flags case-insensitive
class CaseInsensitiveArgumentParser(argparse.ArgumentParser):
    """ Override to Argparse to enable case insensitive arguments """
    def _get_option_tuples(self, option_string):
        # Normalize the option string to lowercase for case-insensitive matching
        option_string = option_string.lower()
        return super()._get_option_tuples(option_string)

#
# Create an Array we use for the Optical Illusion Data
#
def create_array(size :int):
    """Create a 2D array of given size filled with spaces."""
    return [[' ' for _ in range(size)] for _ in range(size)]

#
# Plot Circle Points based on each quadrant and opposite faces.
#
def plot_circle_points(array, cx, cy, x, y):
    """Plot circle points in all octants with boundary checks."""
    max_y = len(array)
    max_x = len(array[0])

    cx = int(cx)
    cy = int(cy)
    x = int(x)
    y= int(y)

    # Bresenhams Opposite points...
    if 0 <= cx + x < max_x and 0 <= cy + y < max_y:
        array[cy + y][cx + x] = '*'
    if 0 <= cx - x < max_x and 0 <= cy + y < max_y:
        array[cy + y][cx - x] = '*'
    if 0 <= cx + x < max_x and 0 <= cy - y < max_y:
        array[cy - y][cx + x] = '*'
    if 0 <= cx - x < max_x and 0 <= cy - y < max_y:
        array[cy - y][cx - x] = '*'
    if 0 <= cx + y < max_x and 0 <= cy + x < max_y:
        array[cy + x][cx + y] = '*'
    if 0 <= cx - y < max_x and 0 <= cy + x < max_y:
        array[cy + x][cx - y] = '*'
    if 0 <= cx + y < max_x and 0 <= cy - x < max_y:
        array[cy - x][cx + y] = '*'
    if 0 <= cx - y < max_x and 0 <= cy - x < max_y:
        array[cy - x][cx - y] = '*'

#
# Use Bresenhams Algorithm to create the points
#
def draw_circle(array, center_x, center_y, radius):
    """Draw a circle on the 2D array using Bresenham's circle algorithm."""
    x = radius
    y = 0
    p = 1 - radius  # Initial decision parameter

    # Draw circle
    plot_circle_points(array, center_x, center_y, x, y)

    while x > y:
        y += 1
        if p <= 0:
            p += 2 * y + 1
        else:
            x -= 1
            p += 2 * y - 2 * x + 1
        plot_circle_points(array, center_x, center_y, x, y)

def draw_diagonals_in_array(width :int, height: int):
    global SVG_ILLUSION_ARRAY

    size = max(width, height)
    SVG_ILLUSION_ARRAY = create_array(size)

    max_range = width + height + 1
    max_y = len(SVG_ILLUSION_ARRAY)
    max_x = len(SVG_ILLUSION_ARRAY[0])

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
                        SVG_ILLUSION_ARRAY[start_y][xpos] = '*'
                                
                start_y += 1

#    print_array(SVG_ILLUSION_ARRAY)


#
# Debugging purposes to see the array...
#
def print_array(array):
    """Print the 2D array."""
    for row in array:
        print(''.join(row))

#
# Write the Final SVG File from Data in the List.
#
from pathlib import Path

def svg_savefile(savename):
    global SVG_CANVAS_WIDTH
    global SVG_CANVAS_HEIGHT

    try:
        output_path = Path(savename).resolve()

        with output_path.open('w', encoding="utf-8") as fp:
            fp.write(SVG_HEADER)
            fp.write(f'<svg width="{SVG_CANVAS_WIDTH:.2f}mm" height="{SVG_CANVAS_HEIGHT:.2f}mm" xmlns="http://www.w3.org/2000/svg">\n')
            fp.write(''.join(SVG_DATA_LIST))
            fp.write('</svg>\n')

        print(f"\n✅ Written file: {output_path}")

    except PermissionError:
        print(f"❌ Permission denied when writing to {savename}. Is it open in another application?")
        if DEBUG:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
    except IOError as error:
        print(f"❌ File I/O error: {error}")
        if DEBUG:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
    except Exception as error:
        print(f"❌ Unexpected error: {error}")
        if DEBUG:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)


#
# Update Canvas Width/Height
#
def update_svg_canvas_dimensions(width, height):
    global SVG_CANVAS_WIDTH
    global SVG_CANVAS_HEIGHT

    if width > 405:
        print
    if width > SVG_CANVAS_WIDTH:
        SVG_CANVAS_WIDTH = width

    if height > SVG_CANVAS_HEIGHT:
        SVG_CANVAS_HEIGHT = height

#
# Add Centred Text
#
def add_svg_centeredText(x, y, text, fill_colour):

    text_str = (f'\t\t<text x="{x:.3f}mm" y="{y:.3f}mm" text-anchor="middle" '
                f'dominant-baseline="central" fill="none" stroke = "{fill_colour}" '
                f'stroke-width="0.5px" alignment-baseline="middle" font-size="24pt"'
                f'>{text} </text>\n'
    )

    return text_str

#
# Add Centred Text
#
def add_svg_centeredCircle(x, y, radius = 5.0, fill_colour = "#000000", stroke_width = 0.0, stroke = "#000000"):

    circle_str = (f'\t\t<circle cx="{x:.3f}mm" cy="{y:.3f}mm" r="{radius:.3f}mm" fill="{fill_colour}" ')
    if stroke_width != 0.0:
        circle_str += f'stroke="{stroke}" stroke-width="{stroke_width}mm" '


    return circle_str + "/> \n"

#
# Add rectangle
#
def add_svg_rectangle(id, x, y, width, height, rx=0.0, ry=0.0, fill_colour="#000000", opacity = 100.0, stroke_width = 0.0, stroke_colour = "#000000"):
    # Base rectangle attributes
    rect_str = ('\t\t<rect ')

    if len(id)>0:
        rect_str += f'id="{id}" '

    rect_str += (f'width="{width:.3f}mm" height="{height:.3f}mm" '
                f'x="{x:.3f}mm" y="{y:.3f}mm" ')
    
    # Add rx and ry only if they're non-zero
    if rx != 0.0:
        fx = abs(width * (rx/100.0) / 2)
        rect_str += f'rx="{fx:.3f}mm" '
    if ry != 0.0:
        fy = abs(height * (ry/100.0) / 2)
        rect_str += f'ry="{fy:.3f}mm" '

    # Add stroke attributes if stroke width is not 0
    if stroke_width != 0.0:
        #rect_str += f'stroke-width="{stroke_width}" stroke="{stroke_colour}" stroke-opacity="100%" '
        rect_str += f'style="fill:none;stroke:{stroke_colour};stroke-width:{stroke_width}mm; " '
    else:
        # Add opacity only if it's not 100%
        if opacity != 100.0:
            rect_str += f'opacity="{opacity}" '

        rect_str += f'fill="{fill_colour}" '
        #style="fill:none;stroke:rgb(35,31,32);stroke-width:12.5px;"

    # Close the rect tag
    rect_str += '/>\n'
    
    # Update canvas dimensions if needed
    #update_svg_canvas_dimensions(x + width, y + height)
    
    return rect_str

#
# Create an SVG File sized for the Range 400mm Frames
#   Current loading is the internal frame has a useable 397mm
#       with 405mm on outer frame before backing board.
#
def create_svg_frame400(Outline_Only = True, 
                        add_PNG = False, 
                        rect_radius_x = 25, 
                        rect_radius_y = 25):
    """Create the SVG File data to create guides and cutmarks for a 400mm frame supplied
        by The Range... They ofer a few, the latest one has a useable 
        inner area of 397mm
        outer area of 405mm (Maximum for the Mountboard to fit)
        This will need updating when I add more frames"""
    global SVG_DATA_LIST

    # Useable Area of the Frame
    useableArea = 397.00
    outerFrame  = 405.00

    # Get the number of Pixels plus border of 2
    if Image_Real_Width > 0:
        multiplier = int(max (Image_Real_Width + 4, Image_Real_Height + 4))
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
    CutGuides.append(add_svg_rectangle("TopRightGuide",SVG_CANVAS_WIDTH - 60.0, 0.0, 60.0, 60.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))
    CutGuides.append(add_svg_rectangle("BottonLeftGuide",0.0, SVG_CANVAS_HEIGHT - 60.0, 60.0, 60.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))
    CutGuides.append(add_svg_rectangle("BottomRightGuide",SVG_CANVAS_WIDTH - 60.0, SVG_CANVAS_HEIGHT - 60.0, 60.0, 60.0, 0.0, 0.0, "#FFFFFF", 0.0, 1, "#000000"))

    CutGuides.append(f'\t</g>\n')

    SVG_DATA_LIST.append(''.join(CutGuides))



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
    
    global SVG_DATA_LIST, ILLUSION_TYPE_CIRCLE

    totalWidth = rect_width * width + abs(startX * 2)
    totalHeight = rect_height * height + abs(startY * 2)

    # Update the Canvas size, just incase...     
    update_svg_canvas_dimensions(totalWidth, totalHeight)


    # Create Illusion Data
    if ILLUSION_TYPE_CIRCLE:
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
        SVG_DATA_LIST.append(''.join(fill_group))

    SVG_DATA_LIST.append(''.join(dark_group))
    SVG_DATA_LIST.append(''.join(light_group))

    if add_PNG:
        offsetX = math.ceil((width - Image_Real_Width) / 2)
        offsetY = math.ceil((height - Image_Real_Height) / 2)
        sprite_Data = create_svg_data_for_loaded_PNG(outline_only, use_real_colours,
                                                     offsetX, offsetY,
                                                     rect_width , rect_height,
                                                     rect_radius_x, rect_radius_y,
                                                     startX, startY)
        SVG_DATA_LIST.append(''.join(sprite_Data))

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
    global SVG_GRID_COUNT
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
            SVG_GRID_COUNT += 1

    dark_group.append("\t</g>\n")
    light_group.append("\t</g>\n")

    return light_group, dark_group

#
# clip the coords for inside the canvas.
#
def ClipDimensions(rect_x, rect_y, rect_width, rect_height, offsetX, offsetY):
    req_width = rect_width
    req_height = rect_height

    # Clip Illusion Squares to image when in frame mode.
    if rect_x < offsetX:
        rect_x = offsetX
        req_width = rect_width - offsetX

    if rect_x + req_width > SVG_CANVAS_WIDTH - offsetX:
        req_width = SVG_CANVAS_WIDTH - offsetX - rect_x

    if rect_y < offsetY:
        rect_y = offsetY
        req_height= rect_height - offsetY

    if rect_y + req_height > SVG_CANVAS_HEIGHT - offsetY:
        req_height = SVG_CANVAS_HEIGHT - offsetY - rect_y

    return rect_x, rect_y, req_width, req_height


#
# Create SVG Data for the Optical Illusion - circles...
#
def create_svg_illusion_data_circular(outline_only = False, width = 20, height = 20, rect_width=20.0, rect_height=20.0, rect_radius_x = "25%", rect_radius_y = "25%", offsetX = 0.0, offsetY = 0.0):
    global SVG_ILLUSION_ARRAY, SVG_DARK_COUNT, SVG_LIGHT_COUNT

    width = int(width)
    height = int(height)

    size = max(width, height)
    SVG_ILLUSION_ARRAY = create_array(size)

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
            draw_circles = circle_streak < ILLUSION_MAX_STREAK
            if not draw_circles:
                circle_streak = 0
                none_circle_streak = 1
        else:
            none_circle_streak, circle_streak = none_circle_streak + 1, 0
            draw_circles = none_circle_streak > ILLUSION_MAX_STREAK
            if draw_circles:
                circle_streak = 1
                none_circle_streak = 0

        if draw_circles:
            draw_circle(SVG_ILLUSION_ARRAY, cx, cy, radius)

    print_array(SVG_ILLUSION_ARRAY)

    fill_group = [f'\t<g id="OpticalIllusionCirclesAll">\n']
    for y in range (height):
        for x in range(width):
            sample = SVG_ILLUSION_ARRAY[y][x]
            if sample != " ":
                fillColour = "#000000"
                SVG_DARK_COUNT += 1
            else:
                fillColour = "#ffffff"
                SVG_LIGHT_COUNT += 1
                    
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
                                                   SVG_ILLUSION_COLOUR_TABLE[DARK_BLOCK_INDEX],
                                                   SVG_ILLUSION_COLOUR_TABLE[LIGHT_BLOCK_INDEX])
 
    return fill_group, light_group, dark_group


#
# Create SVG Data for the Optical Illusion
#
def create_svg_illusion_data_diagonals(outline_only = False, width = 20, height = 20, rect_width=20.0, rect_height=20.0, rect_radius_x = "25%", rect_radius_y = "25%", offsetX = 0.0, offsetY = 0.0):

    global SVG_LIGHT_COUNT, SVG_DARK_COUNT

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
                                                   SVG_ILLUSION_COLOUR_TABLE[DARK_BLOCK_INDEX],
                                                   SVG_ILLUSION_COLOUR_TABLE[LIGHT_BLOCK_INDEX])

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
            draw_line = line_streak <= ILLUSION_MAX_STREAK
            if not draw_line:
                line_streak = 0
                none_line_streak = 1
                #draw_line = True
        else:
            none_line_streak, line_streak = none_line_streak + 1, 0
            draw_line = none_line_streak > ILLUSION_MAX_STREAK
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
                    SVG_DARK_COUNT += 1
                else:
                    SVG_LIGHT_COUNT += 1

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
    
    global SVG_DATA_LIST

    width = Image_Real_Width
    height = Image_Real_Height

    totalWidth = rect_width * width + abs(startX)
    totalHeight = rect_height * height + abs(startY)
    update_svg_canvas_dimensions(totalWidth, totalHeight)

    # Main Optical Illusion Drawing Group
    sprite_group = create_svg_data_for_loaded_PNG(outlineOnly,
                                                  use_real_colours,
                                                  startX, startY,
                                                  rect_width, rect_height,
                                                  rect_radius_x, rect_radius_y)

    SVG_DATA_LIST.append(''.join(sprite_group))

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
    """ Create the SVG Data for the currently loaded PNG Image """

    global SVG_PNG_PIXEL_COUNT
    
    width = Image_Real_Width
    height = Image_Real_Height

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
        row = pattern[int((y+Image_MinY) % pattern_h)]
        for x in range(width):
            pixel, index, fill_color = getPixelFromRow(x + Image_MinX,row,channels, pattern_w )
            # Only Add Pixel if in the Allowed Colour List
            if pixel >=0:
                if not use_real_colours:
                    #fill_color = "#2f0040" if (x % 2) == (y % 2) else "#FF7f80"
                    fill_color = SVG_ILLUSION_COLOUR_TABLE[DARK_PIXEL_INDEX] if ((x+offset_X) % 2) == ((y+offset_Y) % 2) else SVG_ILLUSION_COLOUR_TABLE[LIGHT_PIXEL_INDEX]
                    group = dark_group if (x % 2) == (y % 2) else light_group

                rect_x = (x + offset_X) * rect_width + start_X
                rect_y = (y + offset_Y) * rect_height + start_Y

                SVG_PNG_PIXEL_COUNT += 1
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

# Update Verticies depending on position (0 or non 0)
# Currently Assumes, 0 - Left, non-Zero right
#
def update_vert(val, r1, r2):
    if val > 0.0:
        return r2
    return r1

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
    
    global Current_Face
    global Current_Opposite_Face
    global CurrentZOffset
    global Primitive_Multipler

  #  if not jointFlag:
  #      return ""

    strVertices = f"o Pixel_{primitive_x}_{primitive_y}\n"
    strFaces = ""

    # Get the number of entries for Cube Vertices
    # For future where primitive may change
    vert_len = len(primitive_vert)
    face_len = len(primitive_face)

    rx = primitive_x * CUBE_X * Primitive_Multipler
    ry = primitive_y * CUBE_Y * Primitive_Multipler
    rx2 = rx + (CUBE_X * width * Primitive_Multipler)
    ry2 = ry + (CUBE_Y * height * Primitive_Multipler)

    myFormatter = "{0:.6f}"

    #
    # Generate the Basic Primitive for the Model
    #
    for index in range(vert_len):
        v1 = primitive_vert[index][0] * Primitive_Multipler
        v2 = primitive_vert[index][1] * Primitive_Multipler
        v3 = primitive_vert[index][2] * (Primitive_Layer_Depth/10) #* Primitive_Multipler

        if v3 != 0.0 and primitive_y_multiplier != 1.0:
            v4 = primitive_y_multiplier * v3
            v3 = v4 + CurrentZOffset
        else:
            v3 += CurrentZOffset

        # Yeah, quick and dirty, I need to think this through
        if not jointFlag:
            if modify_Flag:
                v1 = update_vert(v1, rx, rx2)
                v2 = update_vert(v2, ry, ry2)

        else:
            # Invert Jointer Piece Depending on Direction set
            v1 = (jointFlag * v1) + rx + (CUBE_X * Primitive_Multipler)
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

    if material_index > 1:
        print
    if CREATE_MTL_FILE:
        mtl_string = "mtllib "+os.path.basename(mtl_filename) + "\n" + \
            f"usemtl {material_index}\n"

    strFaces=f"g ACIS Pixel_{primitive_x}_{primitive_y}_F\n"

    #
    # Face List may contain variable length face lists.
    #
    for index in range(face_len):
        # Initial Face Identifier
        strFaces = strFaces + "f "

        for faceIndex in range(len(primitive_face[index])):
            
            faceID = primitive_face[index][faceIndex] + Current_Face
            faceIDOpposite = Current_Opposite_Face+faceID
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
    Current_Face += len(primitive_vert)
    Current_Opposite_Face += (len(primitive_normals))
    return Primitive_String

#
# Define Material Colour
#
def MaterialColourAsString(r,g,b):
    global mtl_final_list

    myFormatter = "{0:.6f}"

    mult = 1.0/255.0

    Material = f"\nnewmtl {mtl_current_index}\n" + \
            f"Kd " + str(myFormatter.format(mult * r)) + " " + \
            str(myFormatter.format(mult * g)) + " " + \
            str(myFormatter.format(mult * b)) + " " + \
            default_mtl_params + "\n"
    
    mtl_final_list.append(Material)
    return Material

#
# Add material colour to Material File
#
def addMaterialToFile(r, g, b, pixel =-1):
    global mtl_current_index

    # Check to see if we already have this material.
    ColourCode = "#"+'{:02x}'.format(r)+'{:02x}'.format(g)+'{:02x}'.format(b)

    # Is Pixel in excluded list?
    if ColourCode in Colour_Exclusion_List:
        return False, ColourCode
    
    if len(Colour_Process_Only_list) > 0:
        if ColourCode not in Colour_Process_Only_list:
            return False, ColourCode

    if not ColourCode in mtl_colour_dict and not ColourCode in Colour_Exclusion_List:
        mtl_colour_dict[ColourCode] = 0


        #if CREATE_MTL_FILE == True and pixel >= 0:
        if pixel >= 0:
            
            Material = MaterialColourAsString(r,g,b)
            mtl_current_index += 1
            #WriteToMTLFile(Material)
            return True, ColourCode
        
    return True, ColourCode

#
# Convert Colour To Pixel - Can extend this to exclude colour ranges in future updates.
#
def getPixelFromRow(x, row, channels, rowWidth):
    # Calculate the offset into the ROW for pixel information
    offset_x = (x * channels) % (rowWidth * channels)
    pixel = 0
    ColourCode = "#000000"

    # Need the current Index of Colour or do we? Could use dict len?
    global mtl_current_index
    global Create_Towered_File

    TowerMultiplier = 1.0

    # If Indexed PNG, we're only interested in the index value
    if channels == 1:
        pixel = row[x]

    else:
        # Get the RGB Values from the offset
        r, g, b = row[offset_x:offset_x + 3]

        # Crude but effective as we're only interested in whether colour data
        # is prsent or not to determine whether to add a primitive or not
        pixel = r|g|b

    if channels == 4:
        #Check Alpha
        a = row[offset_x+3]
        # If below the cutoff we set the pixel to 0 (No Colour Data)
        if a <= ALPHACUTOFF:
            pixel = -1
            r = 0
            g = 0
            b = 0

    valid, ColourCode = addMaterialToFile(r, g, b, pixel)

    if not valid:
        pixel =-1


    material_index = -1
    
    # Retrieve the index of the Colour Code from the Dictionary
    if ColourCode in mtl_colour_dict and pixel > -1:
        material_index = list(mtl_colour_dict).index(ColourCode)
        mtl_colour_dict[ColourCode] += 1

    return pixel, material_index, ColourCode

#
# Process a simple set of rules to determine if a Jointer Block is required.
# That is missing diagonal pixes.  It's crude and needs refinement.
#
def CheckJointRequired(x ,y ,row, nextRow, channels, pattern_w):
    isJointRequired = 0

    # Check if we've Reached the boundary of the Sprite Sheet Sprite
    if y > 0 and not (y+1) % Pixel_H:
        return 0
    
    if x>0 and not (x+1) % Pixel_W:
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
# And this is where all that magic happens.
#   A real Python Programmer can probably optimise this using some Python Magic.
#
def main(noframeRequired):

    global WORKING_FILENAME
    global Colour_Exclusion_List
    global Debug_Txt_File
    global Sort_Colours_Flag
    global Sort_Direction
    global FILE_COUNTER
    global Primitive_Multiplier_Background
    global Primitive_Multiplier_Layers
    global CurrentZOffset

    # Create the Background Object File 
    # Flat Structure width and height of PNG Image.
    obj_file = os.path.join(PATTERNS, "{}.obj".format(WORKING_FILENAME))

    if not noframeRequired:
        try:
            # TODO: Add some error checking here, rather than rely on TRY/CATCH Scenarios.
            with open(obj_file,'w') as fp_obj:
                    fp_obj.write(create_primitive(0, 0, pattern_w, pattern_h, cube_vertices, cube_faces, cube_normals, 0, 0, Primitive_Multiplier_Background))
                    fp_obj.flush()
                    fp_obj.close()
                    # Update Current Offset with multiplier requested
                    #CurrentZOffset += (abs(CUBE_Y*Primitive_Multiplier_Background)) # Shift Vertices Up a Layer...
                    #CurrentZOffset += (abs(CUBE_Y*Primitive_Multiplier_Background*Primitive_Multipler)) # Shift Vertices Up a Layer...
                    CurrentZOffset += Primitive_Layer_Depth*Primitive_Multiplier_Background # Shift Vertices Up a Layer...
                
        except Exception as error:
        # Bad Practice I know...
            print(f"Failed to create Initial file: {obj_file}, error: {error}")
            exit(0)


    ToSort = {}

    if len(Colour_Process_Only_list) > 0:
        SortedColours = list(Colour_Process_Only_list)
        for x in range(0,len(Colour_Process_Only_list)):
            ToSort[Colour_Process_Only_list[x]] = x
    else:
        # Set the Sorted Colours Dictionary to Default
        # Remove any layes that have no pixels
        # Colour layers that are all below the Alpha Threshold will have a count of 0
        for key in mtl_colour_dict:
            if mtl_colour_dict[key] > 0:
                ToSort[key] = mtl_colour_dict[key]
            else:
                print(f"Removing Colour: {key} from processing, pixel count of Zero Detected (Check Alpha Threshold If Required)")

    # Check if we want to sort by Highest Colour Count First
    if Sort_Colours_Flag:
        #SortedColours = {key: val for key, val in sorted(mtl_colour_dict.items(), key = lambda ele: ele[1], reverse=Sort_Direction)}
        SortedColours = {key: val for key, val in sorted(ToSort.items(), key = lambda ele: ele[1], reverse=Sort_Direction)}
    else:
        SortedColours = dict(ToSort)

    # Remove Colours from Excluded List 
    for excluded in Colour_Exclusion_List:
        if excluded in SortedColours:
            del SortedColours[excluded]

    print("Layer Order:")
    for nextLayer in SortedColours:
        print(f"{nextLayer}")

    print(f"       Found : {len(mtl_colour_dict)} Colours")
    print(f"Working with : {len(SortedColours)} Colours\n")

    FILE_COUNTER +=1

    if Create_Layered_File:
        while len(SortedColours) > 0:
            nextLayer = list(SortedColours.keys())[0]
            log(f"Processing Colour: {nextLayer}")

            if nextLayer in mtl_colour_dict:
                if ColoursOnSingleLayerHeight:
                    resp = processFile(nextLayer, nextLayer, Colour_Exclusion_List, Primitive_Multiplier_Layers)
                else:
                    resp = processFile(nextLayer, SortedColours, Colour_Exclusion_List, Primitive_Multiplier_Layers)
                
                if resp == False:
                    print("Failed to process file:")
                    exit (0)
            else:
                print(f"Colour: {nextLayer} is not present, skipping...")
            # Add colour to excluded list to avoid repeat processing
            Colour_Exclusion_List+=[nextLayer]
            del SortedColours[nextLayer]
    else:
        resp = processFile(list(SortedColours.keys())[0], SortedColours, Colour_Exclusion_List)

#
# Load PNG File to Memory and perform some initial processing
#   Check number of Channels, is Alpha Available, discover all colours in image
#
def loadPNGToMemory(Filename):
    # Load the PNG File, Check if Valid
    global pattern, pattern_w, pattern_h, pattern_meta, channels

    pattern, pattern_w, pattern_h, pattern_meta = load_pattern(Filename)

    # If File Wasn't Found Time to Quit
    if pattern == None:
        return False
    
    # Check we're dealing with 8 Bits per channel.
    if pattern_meta['planes'] < 3:
        log(f"PNG File Unsupported, convert to 8 Bits per Channel - 24 bit")
        return False

    # Check if We've loaded a Valid PNG File
    if pattern is None:
        log(f"File: {Filename} is not a valid PNG File")
        return False

    # Check to see if Alpha Byte Present and set number of channels accordingly
    alpha = pattern_meta['alpha']
    channels = 4 if alpha else 3

    discoverPixelLayers()

    return True

# Work out the number of colours in the PNG
# Also the True Width/Height taking out Pixels with Alpha Channels
def discoverPixelLayers():
    # Work our way through each row of the PNG File.
    global Image_MinX
    global Image_MaxX
    global Image_MinY
    global Image_MaxY
    global Image_Real_Width
    global Image_Real_Height
    global Image_Total_Colours

    minx = 999999999
    maxx = 0
    miny = 999999999
    maxy = 0 
    for y in range(pattern_h):
        row = pattern[int(y % pattern_h)]

        for x in range(pattern_w):
            # Get Pixel from Row
            pixel = getPixelFromRow(x, row, channels, pattern_w)[0]

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

    Image_MinX = minx
    Image_MaxX = maxx
    Image_MinY = miny
    Image_MaxY = maxy
    Image_Real_Width = maxx - minx + 1
    Image_Real_Height = maxy - miny + 1

def displayColourInformation():
    SortedColours = {key: val for key, val in sorted(mtl_colour_dict.items(), key = lambda ele: ele[1], reverse=True)}
    
    print("         Layer Order :")
    print("         -------------")
    print()
    print("         Colour Code : Number of Pixels")
    print("         -----------   ----------------\n")   
    for nextLayer in SortedColours:
        print(f"             {nextLayer} : {SortedColours[nextLayer]}")

    print(f"\n               Found : {len(mtl_colour_dict)} Colours")

    
def processFile(colourMatch, allowedDictionary, excludedColours, primitive_y_multiplier=1.0):
    global WORKING_FILENAME
    global Debug_Txt_File
    global CurrentZOffset
    global Primitive_Multiplier_Layers
    global Primitive_Layer_Depth
    global Primitive_Initial_Layer_Depth
    global Create_Towered_File
 
    # Used to define the Current Face Counter
    # Needed to ensure Vertices are correctly defined.
    global Current_Face
    global Current_Opposite_Face
    
    Current_Face = 0
    Current_Opposite_Face = 0

    thisColour = 1

    # Total Number of Primitives Created
    Total_Primitives = 0

    # Define RGB Colours as 0
    r, g, b, a = 0, 0, 0, 255

    global mtl_filename
    global FILE_COUNTER

    global lastPixelFound

    # Define output Filenames based on Input, creating
    #   an  OBJ file with 3D Mesh Details
    #       TXT file with pixel data as seen

    TowerMultiplier = 1.0
    LastTowerMultiplier = 1.0

    if Create_Layered_File:
        obj_file = os.path.join(PATTERNS, "{}_Y{}{}.obj".format(WORKING_FILENAME,FILE_COUNTER,str(colourMatch)))
    else:
        obj_file = os.path.join(PATTERNS, "{}_Y{}.obj".format(WORKING_FILENAME,FILE_COUNTER))

    if Debug_Txt_File:
        txt_file = os.path.join(PATTERNS, "{}_Y{}{}.txt".format(WORKING_FILENAME,FILE_COUNTER,str(colourMatch)))

    # If we're adding Jointer Blocks this will be required.
    LastRow = False

    # open files for Writing, Note we're not checking their presence as we're overwriting/creating
    #   from scratch each time.
    try:
        if Debug_Txt_File:
           fp_txt=open(txt_file,'w')
           log(f"Creating Debug File: {txt_file}")
    except Exception as error:
        print(f"Failed to Create Debug file: {txt_file}\n")
        exit(0)

    try:
        # TODO: Add some error checking here, rather than relay on TRY/CATCH Scenarios.
        with open(obj_file,'w') as fp_obj:
            log(f"Creating Object File: {obj_file}")
                # Create Header for OBJ File
            header = (
                "# Created using PNG2OBJ.py - © Jason Brooks 2022-2025\n"
                f"# Generated on: {datetime.now()}\n"
                f"# Original File: {WORKING_FILENAME}.png, Width: {pattern_w}, Height: {pattern_h}\n"
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
            for y in range(Image_MinY, Image_MaxY + 1):
                row = pattern[int(y % pattern_h)]
                
                # Get Next Row for Jointer Block Processing.
                # We're cheating by MOD by the PNG Height
                # But will set the Last row flag so we don't 
                # Process the rules for this. 
                nextRow = pattern[int((y+1) % pattern_h)]

                if Debug_Txt_File:
                    fp_txt.write('\n')

                # Check If We're processing the last row of Pixels
                if y == (pattern_h-1):
                    LastRow = True

                # If we're splitting models based on pixel width and height add and extra line
                #   And ensure we start the next primitive further down to enforce a gap in the model
                if y >0 and not(y % Pixel_H):
                    start_y = start_y + 1
                    if Debug_Txt_File:
                        fp_txt.write('\n')
                
                # Iterate through the data with
                start_x = 0
                pixel_found = False
                pixel_found_colour_index = 0
                primitive_width = 0
                primitive_x = 0
                lastPixelFound = -1
                LastTowerMultiplier = 1.0
                TowerMultiplier = 1.0

                #for x in range(pattern_w):
                for x in range(Image_MinX,Image_MaxX + 1):
                    # Check if We're Adding extra space between each sprite based
                    #   on fixed pixel width per sprite.
                    if x > 0 and not(x % Pixel_W):
                        if Debug_Txt_File:
                            fp_txt.write("|")

                        # Close off this sprite.
                        if pixel_found:
                            thisColour = pixel_found_colour_index
                            if Create_Layered_File:
                                thisColour = list(mtl_colour_dict).index(colourMatch)
                            pixel_found = False
                            fp_obj.write( create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, cube_normals, False, thisColour, primitive_y_multiplier * TowerMultiplier) )
                            Total_Primitives += 1
                        # Reset Start Position of next Sprite
                        start_x=start_x+1
                        primitive_width = 0
                        primitive_x = start_x
                        lastPixelFound = -1

                    # Get Pixel from Row
                    pixel,mi, mm = getPixelFromRow(x, row, channels, pattern_w)

                    if Create_Towered_File:
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
                        if Debug_Txt_File:
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
                                    if Create_Layered_File:
                                        thisColour = list(mtl_colour_dict).index(colourMatch)
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
                            if Create_Layered_File:
                                thisColour = list(mtl_colour_dict).index(colourMatch)
                            #fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False , pixel_found_colour_index) )
                            fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, cube_normals, False , thisColour, primitive_y_multiplier * LastTowerMultiplier) )
                            pixel_found = False
                            primitive_width = 0
                            Total_Primitives += 1

                        if Debug_Txt_File:
                            fp_txt.write(" ")

                    # Check if we're to add Jointer Blocks
                    if JOINTS_REQUIRED and not LastRow:
                        # Check if Blocks meet the Jointer rule
                        newJoint = CheckJointRequired(x, y, row, nextRow, channels, pattern_w)

                        if newJoint:
                            fp_obj.write(  create_primitive(start_x, start_y + 1, 1, 1, joint_verticies, joint_faces, joint_normals, newJoint, thisColour, primitive_y_multiplier * LastTowerMultiplier) )
                            newJoint = False



                    # Update X Position (Taking into account an offset if we're adding space between sprites)
                    start_x = start_x + 1

                # Update to the next Y Postion and check if we have an unwritten primitive to complete
                if pixel_found:
                    thisColour = pixel_found_colour_index
                    if Create_Layered_File:
                        thisColour = list(mtl_colour_dict).index(colourMatch)
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

            log(f"Successfully Created Object File: {obj_file}\n")

    except Exception as error:
    # Bad Practice I know...
       print(f"Failed to write file: {obj_file}",obj_file)
       print(f"Exception: {error}")
       return False
    

    # Update Current Offset with multiplier requested

    if not ColoursOnSingleLayerHeight:
        #CurrentZOffset += (abs(Primitive_Multipler*primitive_y_multiplier*CUBE_Y)) # Shift Vertices Up a Layer...
        CurrentZOffset += Primitive_Layer_Depth * Primitive_Multiplier_Layers

        # Bit of a bodge, but set the next layer height depth going forward.
        if Primitive_Initial_Layer_Depth != 0.0:
            Primitive_Layer_Depth = Primitive_Initial_Layer_Depth
            Primitive_Initial_Layer_Depth = 0.0

    # Write and Flush the TXT File
    if Debug_Txt_File:
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
    global lastPixelFound

    if pixel <0:
        return False
    
    if len(allowedColours) > 0:        
        if Create_Layered_File:
            if currentColour in allowedColours and currentColour not in excludedColours:
                lastPixelFound = currentColour
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
    global lastPixelFound

    if Create_Layered_File:
        if currentColour not in allowedColours:
            return False
        else:
            return True
    
    if currentColour != lastPixelFound:
        lastPixelFound = currentColour
        return False
    
    return True


#
# Load a PNG File
#
def load_pattern(pattern_name):
    pattern_file = os.path.join(PATTERNS, "{}.png".format(Path(pattern_name).with_suffix('')))

    log(f"Attempting to pre-process file: {pattern_file}")
    if os.path.isfile(pattern_file):
        r = png.Reader(file=open(pattern_file, 'rb'))
        pattern_w, pattern_h, pattern, pattern_meta = r.read()
        pattern = list(pattern)
        log("Loaded PNG file: {}".format(pattern_file))
        return pattern, pattern_w, pattern_h, pattern_meta
    else:
        log("Invalid PNG file: {}".format(pattern_file))
        return None, 0, 0, None

#
# Write Cached Material Information to Material File if Required
#
def CreateMasterMaterialFileMaster(filename):
    global mtl_final_list

    try:
        output_path = Path(filename).resolve()

        with output_path.open('w', encoding='utf-8') as fp_mtl:
            fp_mtl.write("# Created with PNG2ObjV3.PY (C) Jason Brooks\n")
            fp_mtl.write("# See www.muckypaws.com and www.muckypawslabs.com\n")
            fp_mtl.write("# https://github.com/muckypaws/PNG2OBJ\n\n")

            for _, line in enumerate(mtl_final_list):
                fp_mtl.write(f"{line}")

            fp_mtl.write(f"#\n# Total Material Colours Created: {len(mtl_final_list)}\n#\n")

        print(f"✅ Material file written: {output_path}")

    except PermissionError:
        print(f"❌ Cannot write to {filename} — file is locked or open in another application.")
    except Exception as error:
        print(f"❌ Failed to create Material File: {filename}")
        print(f"Error: {error}")
        if DEBUG:
            import sys
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
        sys.exit(1)

                    
#
# Default Logging Code
#
def log(msg):
    #sys.stdout.write("\n")
    sys.stdout.write(str(datetime.now()))
    sys.stdout.write(": ")
    sys.stdout.write(msg)
    sys.stdout.write("\n")
    sys.stdout.flush()

#
# Position the Vertex Data based on Current X, Y Position on Grid
# And Currently Scaling Factors
#
def PositionDesign(vertices,x,y):
    nextVertices = []
    for index, vertex in list(enumerate(vertices)):
        # Get vertices
        v1 = vertex[0] + (x * CUBE_X)
        v2 = vertex[1] + (y * CUBE_Y)
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

    if len(new_vertices) != 8:
        print(f"Sorry Wrong Input Data: {new_vertices}")
        exit(0)

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

    if len(new_vertices) != 8:
        print(f"Sorry Wrong Input Data: {new_vertices}")
        exit(0)

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
    if len(interimDesign) < 4:
        print(f"Sorry Wrong Input Data: {interimDesign}")
        exit(0)

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
    if len(interimDesign) < 4:
        print(f"Sorry Wrong Input Data: {interimDesign}")
        sys.exit(0)

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
    start_y = offsetY
    for y in range(Image_MinY, Image_MaxY + 1):
        row = pattern[int(y % pattern_h)]

        # If we're splitting models based on pixel width and height add and extra line
        #   And ensure we start the next primitive further down to enforce a gap in the model
        if y >0 and not(y % Pixel_H):
            start_y = start_y + 1
        
        # Iterate through the data with
        start_x = offsetX


        for x in range(Image_MinX,Image_MaxX + 1):
            # Check if We're Adding extra space between each sprite based
            #   on fixed pixel width per sprite.
            if x > 0 and not(x % Pixel_W):
                start_x += 1

            # Get Pixel from Row
            pixel,mi, mm = getPixelFromRow(x, row, channels, pattern_w)

            if checkProcessingRules(allowedDictionary, mm, excludedColours, pixel):
                if pixel > 0:
                    print
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
    try:
        if Create_Layered_File:
            obj_file = Path(PATTERNS) / f"{filename}_Y{FILE_COUNTER}{colourMatch}.obj"
        else:
            obj_file = Path(PATTERNS) / f"{filename}_Y{FILE_COUNTER}.obj"

        obj_file = obj_file.resolve()

        with obj_file.open("w", encoding="utf-8") as fp_obj:
            header = (
                "# Creator PNG2OBJ.py - © Jason Brooks 2022\n"
                f"# {datetime.now()}\n"
                f"# Original File: {WORKING_FILENAME}.png, Width: {pattern_w}, Height: {pattern_h}\n"
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
        if DEBUG:
            import sys
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)
    return False

def CreateOBJFileFromDictionary_old(Filename, vertDict, primitive_y_multiplier, LastTowerMultiplier):
    if Create_Layered_File:
        obj_file = os.path.join(PATTERNS, "{}_Y{}{}.obj".format(Filename,FILE_COUNTER,str(colourMatch)))
    else:
        obj_file = os.path.join(PATTERNS, "{}_Y{}.obj".format(Filename,FILE_COUNTER))

    try:
        # TODO: Add some error checking here, rather than relay on TRY/CATCH Scenarios.
        with open(obj_file,'w') as fp_obj:
        # Create Header for OBJ File
            header = "# Creator PNG2OBJ.py - © Jason Brooks 2022\n# " + str(datetime.now()) + "\n"
            header = header + f"# Original File: {WORKING_FILENAME}.png, Width: {pattern_w}, Height: {pattern_h}\n"
            fp_obj.write( header )

            for index, (key,value) in enumerate(vertDict.items()):
                coords = key.split(":")
                x = int(coords[0])
                y = int(coords[1])
                colourIndex = value[3]

                fp_obj.write( create_primitive(x, y, 1, 1, value[0], value[1], value[2], False , colourIndex, primitive_y_multiplier * LastTowerMultiplier, False))

            fp_obj.flush()
            fp_obj.close()

    except Exception as error:
        # Bad Practice I know...
        print(f"Failed to write file: {obj_file}",obj_file)
        print(f"Exception: {error}")
        return False

#
# Add default Materials to MTL File
#
def addDefaultMaterialColours():
# Black
    addMaterialToFile(0,0,0,0)
    # Red
    addMaterialToFile(255,0,0,0)
    # Green
    addMaterialToFile(0,255,0,0)
    # Blue
    addMaterialToFile(0,0,255,0)
    # Yellow
    addMaterialToFile(255,255,0,0)
    # Purple
    addMaterialToFile(255,0,255,0)
    # Cyan
    addMaterialToFile(0,255,255,0)
    # White
    addMaterialToFile(255,255,255,0)

#
# Can we create a simple parametric set of shapes?
#
def ParametricTest(Filename):
    global Primitive_Layer_Depth
    global Primitive_Multipler

    LastTowerMultiplier = 1.0
    primitive_y_multiplier = 1.0
    Primitive_Layer_Depth = 10.0
    Primitive_Multipler = 1.0

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
    #ApplyPNGColoursToParametricObjects(VerticesDict,-2,-2, Colour_Process_Only_list, Colour_Exclusion_List)
    ApplyPNGColoursToParametricObjects(VerticesDict, 0, 0, Colour_Process_Only_list, Colour_Exclusion_List)

    CreateOBJFileFromDictionary(Filename, VerticesDict, primitive_y_multiplier, LastTowerMultiplier)
    CreateMasterMaterialFileMaster(mtl_filename)

#
# Process SVG Options
#
def process_SVG_File(args):
    global SVG_ILLUSION_COLOUR_TABLE
    global ILLUSION_TYPE_CIRCLE
    global ILLUSION_MAX_STREAK

    if len(args.illusioncolourtable) == 4:
        SVG_ILLUSION_COLOUR_TABLE = args.illusioncolourtable

    if len(args.illusioncolourtable) == 4:
        SVG_ILLUSION_COLOUR_TABLE = args.illusioncolourtable

    if args.colourset > -1:
        SVG_ILLUSION_COLOUR_TABLE = SVG_COLOUR_SETS[args.colourset % len(SVG_COLOUR_SETS)]

    ILLUSION_MAX_STREAK = args.maxstreak if args.maxstreak > 0 else ILLUSION_MAX_STREAK

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
        print(f"     Maximum Illusion Streak : {ILLUSION_MAX_STREAK}")
        print(f"   Minimum Border to Add PNG : {args.minimumborder}")
        print(f"          Minimum Grid Width : {args.minimumgridwidth}")
        print(f"         Minimum Grid Height : {args.minimumgridheight}")
        if args.colourset >= 0:
            print(f"        Colour Set Requested : {args.colourset % len(SVG_COLOUR_SETS)}")

    print(f"              Create Outline : {args.outlineOnly}")
    print(f"             Output Filename : {outfilename}")
    print(f"Open SVG File after creation : {args.svgopen}\n")

    ILLUSION_TYPE_CIRCLE = args.illusioncircle

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
        blocks_horizontal = max((args.minimumborder * 2) + Image_Real_Width, args.minimumgridwidth)
        blocks_vertical = max((args.minimumborder * 2) + Image_Real_Height, args.minimumgridheight)
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
    print(f'     Total PNG Pixels : {SVG_PNG_PIXEL_COUNT}')
    if SVG_GRID_COUNT:
        print(f'     Total Grid Count : {SVG_GRID_COUNT}')
        if SVG_PNG_PIXEL_COUNT:
            print(f'  Total Grid less PNG : {SVG_GRID_COUNT - SVG_PNG_PIXEL_COUNT}')
    if SVG_LIGHT_COUNT:
        print(f'  Total Light Inserts : {SVG_LIGHT_COUNT}')
    if SVG_DARK_COUNT:
        print(f'   Total Dark Inserts : {SVG_DARK_COUNT}')

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
            if DEBUG:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(error).__name__, error)

#
# The actual start of Python Code.
#
if __name__ == "__main__":
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
    parser.add_argument("-sw","--spriteWidth",help="Width of Fixed Sprites in Sprite Sheet",type=int,default=DEFAULT_PIXEL_WIDTH)
    parser.add_argument("-sh","--spriteHeight",help="Height of Fixed Sprites in a Sprite Sheet",type=int,default=DEFAULT_PIXEL_HEIGHT)
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
    JOINTS_REQUIRED = args.joints

    # Check if We're creating the Material File.

    CREATE_MTL_FILE = args.mtl

    Create_Layered_File = args.flat
    Create_Layered_File = args.layered
    Create_Towered_File = args.tower

    ALPHACUTOFF = args.alphacutoff

    Sort_Colours_Flag = args.sort

    Primitive_Multiplier_Background = args.backgroundheight
    Primitive_Multiplier_Layers = args.layermultiplier

    # Ensure we're sorting if only one of the sort flags provided.
    if args.reversesort:
        Sort_Colours_Flag = True
        Sort_Direction = True

    # Ensure the Working Filename Has No Extension.
    if len(args.outfilename[0]) > 0:
        WORKING_FILENAME = Path(args.outfilename[0]).with_suffix('')
    else:
        WORKING_FILENAME = Path(args.filename).with_suffix('')

    # Set Material Filename
    mtl_filename = os.path.join(PATTERNS, "{}.mtl".format(WORKING_FILENAME))


    # First Stage, Get Colours In Memory first and see if we have something
    # Attempt to Load the PNG to memory.
    if loadPNGToMemory(args.filename) == False:
        print(f"Unable to open file: {args.filename}.png")
        exit (0)
    
    if Image_Real_Height < 1 or Image_Real_Width < 1:
        print(f"No Image Data to Process, Quitting...")
        exit(0)

    # Remove Excluded Colours from Process Colours List
    # If user provides both in both tables, we'll force exclusion!
    totalColours = len(mtl_colour_dict)
    for excluded in Colour_Exclusion_List:
        if excluded in mtl_colour_dict:
            totalColours -= 1

    if args.excludelist and not args.listColours:
        print(f"Excluding the following colours: {args.excludelist}\n")
        Colour_Exclusion_List = args.excludelist

    if args.processcolours:
        print(f"Only Processing the following colours: {args.processcolours}")
        Colour_Process_Only_list = args.processcolours

    Debug_Txt_File = args.debug

    Pixel_W = args.spriteWidth
    Pixel_H = args.spriteHeight

    widthMultiplier = 0.01
    heightMultiplier = 0.01

    ColoursOnSingleLayerHeight = args.nextlayeronly



    print("")
    print(f"    Image Information :")
    print("    -------------------\n")
    print(f"           Image File : {args.filename}")
    print(f"       PNG Image Size : {pattern_w}px (width), {pattern_h}px (height)")
    print(f"   Number of Channels : {channels}")
    print("")
    print(f"     Joints Requested : {JOINTS_REQUIRED}\n Create Material File : {CREATE_MTL_FILE}")
    print(f" Reverse Sort Colours : {Sort_Colours_Flag}")
    print(f"Create Flat File Only : {not Create_Layered_File}" )
    print(f"         Alpha Cutoff : {ALPHACUTOFF}")


    if Pixel_W != DEFAULT_PIXEL_WIDTH:
        print(f"   Sprite Sheet Width : {Pixel_W}")
    if Pixel_H != DEFAULT_PIXEL_HEIGHT:
        print(f"  Sprite Sheet Height : {Pixel_H}")

    # Process file parameters for 3D Waveform OBJ Format
    if not args.svg:
        if args.maxheight != 0.0 or args.maxwidth != 0.0:
            # Need to calculate the Multipliers...
            widthMultiplier = args.maxwidth / Image_Real_Width
            heightMultiplier = args.maxheight / Image_Real_Height

            if widthMultiplier == 0.0:
                widthMultiplier = heightMultiplier

            if heightMultiplier == 0.0:
                heightMultiplier = widthMultiplier

            Primitive_Multipler = min(widthMultiplier, heightMultiplier) / 10.0

        # Calculate Layer Depths.
        if args.maxdepth != 0.0:
            # Do we need a fixed First Layer Depth?

            if not Create_Layered_File:
                Primitive_Initial_Layer_Depth = args.maxdepth
                Primitive_Layer_Depth = Primitive_Initial_Layer_Depth
            else:
                # If we didn't pass an colours to process (So all except the exception list)
                if args.initialLayerDepth != 0.0 and totalColours > 0 and len(args.processcolours) == 0:
                    # How many colours are we processing?
                    # If more than one, set layer heights accordingly.
                    if totalColours > 1:
                        Primitive_Initial_Layer_Depth = (args.maxdepth - args.initialLayerDepth)/(len(mtl_colour_dict)-1)
                        Primitive_Layer_Depth = args.initialLayerDepth
                    else:
                        # Only one colour to process so has to be maximum height.
                        Primitive_Initial_Layer_Depth = args.maxdepth
                        Primitive_Layer_Depth = Primitive_Initial_Layer_Depth
                    CurrentZOffset = 0.0

                if args.initialLayerDepth != 0.0 and len(Colour_Process_Only_list) > 1 and len(args.processcolours) > 0:
                    # Set height of initial layer depth
                    Primitive_Layer_Depth = args.initialLayerDepth
                    Primitive_Initial_Layer_Depth = (args.maxdepth - args.initialLayerDepth) / (len(Colour_Process_Only_list) - 1)
                    #Primitive_Layer_Depth = Primitive_Initial_Layer_Depth
                    CurrentZOffset = 0.0
                else:
                    #if len(Colour_Process_Only_list) > 0:
                    if Primitive_Layer_Depth == 0.0:
                        if len(Colour_Process_Only_list):
                            Primitive_Layer_Depth = args.maxdepth / len(Colour_Process_Only_list)
                        else:
                            Primitive_Layer_Depth = args.maxdepth / totalColours

        else:
            Primitive_Layer_Depth = abs(Primitive_Multipler*CUBE_Y)

        if args.startZ != 0.0:
            CurrentZOffset = args.startZ

        print(f"Background Multiplier : {Primitive_Multiplier_Background:.2f}")
        print(f"     Layer Multiplier : {Primitive_Multiplier_Layers:.2f}")
        print(f"       Object Start Z : {args.startZ:.2f}mm")
        print(f" Object Max Depth (Z) : {args.maxdepth:.2f}mm")
        if Primitive_Initial_Layer_Depth != 0.0:
            print(f"      First Layer Depth : {Primitive_Layer_Depth:.2f}mm")
            print(f"      Next Layer Depths : {Primitive_Initial_Layer_Depth:.2f}mm")

        else:
            print(f"     Each Layer Depth : {Primitive_Layer_Depth:.2f}mm")

        if len(Colour_Process_Only_list) > 0:
            print(f"     Requested Layers : {len(Colour_Process_Only_list)}")

        print(f"     Background Frame : {not args.noframe}")

        if ColoursOnSingleLayerHeight:
            print(f"\n **** Seperate Colours On Single Layer Selected ****")


    if pattern_w != Image_Real_Width or pattern_h != Image_Real_Height:
        print(f"\n   Actual Image Width : {Image_Real_Width} Pixels")
        print(f"  Actual Image Height : {Image_Real_Height} Pixels")
        print(f"        Image Start X : {Image_MinX}")
        print(f"        Image Start Y : {Image_MinY}")
        print(f"         Bounding Box : ({Image_MinX},{Image_MinY},{Image_MaxX},{Image_MaxY}) ")

    if ThreeD:
        print(f"\n  Pixel Width/Height : {widthMultiplier:.2f}mm x {heightMultiplier:.2f}mm")
    else:
        print("\n            Requested : ")
        print(f"   Pixel Width/Height : {args.svg_pixel_width:.2f}mm x {args.svg_pixel_height:.2f}mm")
        print(f"          Rect Radius : {args.svg_radius_percent_x:.2f}% x {args.svg_radius_percent_y:.2f}%")

    if Debug_Txt_File:
        print(f"\n      Debug Text File : {Debug_Txt_File}\n")

    if len(Colour_Exclusion_List) > 0:
        print(f"\nColour list to exclude: {Colour_Exclusion_List}")
    if len(Colour_Process_Only_list) > 0:
        print(f"\n   Colours to process : {Colour_Process_Only_list}")

    print("\n")

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
        CreateMasterMaterialFileMaster(mtl_filename)
