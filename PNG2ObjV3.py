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
from png2obj import runtime
from png2obj.imageprocessing import loadPNGToMemory
from png2obj.objectcreation import (
    CreateMasterMaterialFileMaster,
    ParametricTest,
    addDefaultMaterialColours,
    displayColourInformation,
    main,
)
from png2obj.svg import process_SVG_File

# Application Defaults
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

    # --- Scope C: validate / clamp numeric arguments ---------------------
    # Valid inputs are left untouched; only out-of-range values are corrected
    # (alphacutoff) or rejected with a clear message. Rejections go through
    # parser.error(), which prints to stderr and exits with code 2.
    _arg_errors = []

    # alphacutoff is a 0-255 byte threshold; clamp anything outside that range.
    if args.alphacutoff < 0 or args.alphacutoff > 255:
        _clamped = max(0, min(255, args.alphacutoff))
        print(
            f"Warning: --alphacutoff {args.alphacutoff} is outside 0-255; "
            f"clamping to {_clamped}."
        )
        args.alphacutoff = _clamped

    # Dimensions / depths / Z start must not be negative.
    for _flag, _val in (
        ("--maxwidth", args.maxwidth),
        ("--maxheight", args.maxheight),
        ("--maxdepth", args.maxdepth),
        ("--initialLayerDepth", args.initialLayerDepth),
        ("--startZ", args.startZ),
    ):
        if _val < 0:
            _arg_errors.append(f"{_flag} must not be negative (got {_val})")

    # Sprite tile sizes must be a positive number of pixels. A value of 0 would
    # trigger a modulo-by-zero while scanning sprite boundaries, so reject < 1.
    for _flag, _val in (
        ("--spriteWidth", args.spriteWidth),
        ("--spriteHeight", args.spriteHeight),
    ):
        if _val < 1:
            _arg_errors.append(f"{_flag} must be a positive integer (got {_val})")

    # Height multipliers must be non-negative to produce sane geometry.
    for _flag, _val in (
        ("--backgroundheight", args.backgroundheight),
        ("--layermultiplier", args.layermultiplier),
    ):
        if _val < 0:
            _arg_errors.append(f"{_flag} must not be negative (got {_val})")

    if _arg_errors:
        parser.error("invalid argument value(s): " + "; ".join(_arg_errors))



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
