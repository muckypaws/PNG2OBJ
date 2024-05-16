#!/usr/bin/env python3
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
#
# Usage :-
#   PNG2OBJ.py Filename
#
#   i.e. ./PNG2OBJ SpriteSheet
#
#   Do not include the File Extension - Lazy I know...
#
#   Two output files are created
#
#       Filename.obj    <-- Contains the WaveFront OBJ 3D Vertices information
#       Filename.txt    <-- Used for debugging, showing an ASCII representation
#                           Of what pixels were processed.
#       Filename.mtl    <-- Contains the Wavefront Material File information.

import argparse         # 'bout time I added Parsing...
from datetime import datetime
import os
import sys
import png

# Application Defaults

# Default location for File
#PATTERNS = "./"
PATTERNS=""

DEFAULT_PIXEL_WIDTH  = 4096
DEFAULT_PIXEL_HEIGHT = 4096

# Set Pixel Width and Height if Sprites are fixed width within the sheet, otherwise 
# use a high number.
Pixel_W = DEFAULT_PIXEL_WIDTH
Pixel_H = DEFAULT_PIXEL_HEIGHT

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
ALPHACUTOFF = 254

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

# Basic Definition for a Jointer Cube Where Pixels are connected by Corners Only
# This is needed if there's no overlap on your printer and want to ensure a 
# a connection that should lift off the printer.


joint_verticies = ( [ -1.414213, -0.000000,  0.000000],
                    [ -1.414213, -0.000000, 10.000000],
                    [  0.000000, -0.000000,  0.000000],
                    [  0.000000, -0.000000, 10.000000],
                    [  0.000000,  1.414214, 10.000000],
                    [  0.000000,  1.414214,  0.000000],
                    [  1.414213, -0.000000,  0.000000],
                    [  0.000000, -1.414214,  0.000000],
                    [  0.000000, -1.414214, 10.000000],
                    [  1.414213, -0.000000, 10.000000])




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
# Define the Colour Dictionary
#
mtl_colour_dict   = {}
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
Primitive_Multipler = 1.0

# Object Z Multiplier for each layer
Primitive_Layer_Depth = 0.0

# If we need a specific Initial Layer, this will override.
Primitive_Initial_Layer_Depth = 0.0

# Create a Single Layered File with Object Heights Dependent on Colour Order
# provided in the Process Colour Order list
Create_Towered_File = False

# Update Verticies depending on position (0 or non 0)
def update_vert(val,r1,r2):
    if val > 0.0:
        return r2
    return r1

#
# Create a Primitive, in this example a Cube, but could be swapped for
#   Any primitive type
#
def create_primitive(primitive_x, primitive_y,
                     width, height,
                     primitive_vert,
                     primitive_face,
                     primitive_normals,
                     jointFlag, material_index,
                     primitive_y_multiplier=1.0):
    
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

    #rx = primitive_x  * Primitive_Multipler
    #ry = primitive_y  * -Primitive_Multipler
    #rx2 = rx + (width * Primitive_Multipler)
    #ry2 = ry + (height * -Primitive_Multipler)

    myFormatter = "{0:.6f}"

    #
    # Generate the Basic Primitive for the Model
    #
    for index in range(vert_len):
        v1 = primitive_vert[index][0] * Primitive_Multipler
        v2 = primitive_vert[index][1] * Primitive_Multipler
        v3 = primitive_vert[index][2] * (Primitive_Layer_Depth/10)

        if v3 != 0.0 and primitive_y_multiplier != 1.0:
            v4 = primitive_y_multiplier * v3
            v3 = v4 + CurrentZOffset
        else:
            v3 += CurrentZOffset

        # Yeah, quick and dirty, I need to think this through
        if not jointFlag:
            v1 = update_vert(v1, rx, rx2)
            v2 = update_vert(v2, ry, ry2)
        else:
            # Invert Jointer Piece Depending on Direction set
            v1 = (jointFlag * v1) + rx + CUBE_X
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

    if CREATE_MTL_FILE:
        mtl_string = "mtllib "+os.path.basename(mtl_filename) + "\n" + \
            f"usemtl {material_index}\n"
    mtl_string = "mtllib "+os.path.basename(mtl_filename) + "\n" + \
            f"usemtl {material_index}\n"
    strFaces=f"g ACIS Pixel_{primitive_x}_{primitive_y}_F\n"
    for index in range(face_len):
        f1 = primitive_face[index][0] + Current_Face
        f2 = primitive_face[index][1] + Current_Face
        f3 = primitive_face[index][2] + Current_Face

        #strFaces = strFaces + "f " + f"{f1}//{f1} {f2}//{f2} {f3}//{f3}\n"
        if jointFlag:
            strFaces = strFaces + "f " + f"{f1}//{Current_Opposite_Face + f1} {f2}//{Current_Opposite_Face + f2} {f3}//{Current_Opposite_Face + f3}\n"
        else:
            strFaces = strFaces + "f " + f"{f1}//{(index*3)+1+ Current_Opposite_Face} {f2}//{(index*3)+2+ Current_Opposite_Face} {f3}//{(index*3)+3+ Current_Opposite_Face}\n"

    Primitive_String = strVertices + strNormals + mtl_string + strFaces + "# "+str(face_len)+" Faces\n\n"


    # update face Index Counter to next set 
    #Current_Face += (face_len * 2)
    #Current_Face += 8
    Current_Face += len(primitive_vert)
    Current_Opposite_Face += (len(primitive_normals))
    return Primitive_String

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


    # Check to see if we already have this material.
    ColourCode = "#"+'{:02x}'.format(r)+'{:02x}'.format(g)+'{:02x}'.format(b)

    if not ColourCode in mtl_colour_dict: # and not ColourCode in Colour_Exclusion_List:
        mtl_colour_dict[ColourCode] = 0
        
        if CREATE_MTL_FILE == True:
            myFormatter = "{0:.6f}"

            mult = 1.0/255.0

            Material = f"\nnewmtl {mtl_current_index}\n" + \
                    f"Kd " + str(myFormatter.format(mult * r)) + " " + \
                    str(myFormatter.format(mult * g)) + " " + \
                    str(myFormatter.format(mult * b)) + " " + \
                    default_mtl_params + "\n"

            WriteToMTLFile(Material)
            mtl_current_index += 1

    material_index = 0
    
    # Retrieve the index of the Colour Code from the Dictionary
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

    if (a > 0 and d > 0 and b == 0 and c == 0):
        isJointRequired = 1

    if (b > 0 and c > 0 and a == 0 and d == 0):
        isJointRequired = -1

    return isJointRequired

#
# Write to the MTL File Appending
#
def WriteToMTLFile(text):
    global mtl_filename
    with open(mtl_filename,'a') as fp_mtl:
        fp_mtl.write(text)
        fp_mtl.write("\n")
        fp_mtl.flush()
        fp_mtl.close()

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
        ToSort = dict(mtl_colour_dict)

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
            print(f"Processing Colour: {nextLayer}")


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
def loadPNGToMemory():
    global WORKING_FILENAME
    # Load the PNG File, Check if Valid
    global pattern, pattern_w, pattern_h, pattern_meta, channels

    pattern, pattern_w, pattern_h, pattern_meta = load_pattern(WORKING_FILENAME)

    # If File Wasn't Found Time to Quit
    if pattern == None:
        return False
    
    # Check we're dealing with 8 Bits per channel.
    if pattern_meta['planes'] < 3:
        log(f"PNG File Unsupported, convert to 8 Bits per Channel - 24 bit")
        return False

    # Check if We've loaded a Valid PNG File
    if pattern is None:
        log(f"File: {WORKING_FILENAME} is not a valid PNG File")
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
    except Exception as error:
        print(f"Failed to Create Debug file: {txt_file}\n")
        exit(0)

    try:
        # TODO: Add some error checking here, rather than relay on TRY/CATCH Scenarios.
        with open(obj_file,'w') as fp_obj:

                # Create Header for OBJ File
            header = "# Creator PNG2OBJ.py - © Jason Brooks 2022\n# " + str(datetime.now()) + "\n"
            header = header + f"# Original File: {WORKING_FILENAME}.png, Width: {pattern_w}, Height: {pattern_h}\n"
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



    except Exception as error:
    # Bad Practice I know...
       print(f"Failed to write file: {obj_file}",obj_file)
       print(f"Exception: {error}")
       return False
    

    # Update Current Offset with multiplier requested

    if not ColoursOnSingleLayerHeight:
        #CurrentZOffset += (abs(Primitive_Multipler*primitive_y_multiplier*CUBE_Y)) # Shift Vertices Up a Layer...
        CurrentZOffset += Primitive_Layer_Depth

        # Bit of a bodge, but set the next layer height depth going forward.
        if Primitive_Initial_Layer_Depth != 0.0:
            Primitive_Layer_Depth = Primitive_Initial_Layer_Depth
            Primitive_Initial_Layer_Depth = 0.0

    # Write and Flush the TXT File
    if Debug_Txt_File:
        fp_txt.write('\n')
        fp_txt.flush()
        fp_txt.close()

    if CREATE_MTL_FILE:
        FinaliseMasterMaterialFile(mtl_filename)
    return True

#
# Check Processing Rule to Create Objects
#
def checkProcessingRules(allowedColours, currentColour, excludedColours, pixel):
    global lastPixelFound

    if pixel <0:
        return False
    
    if Create_Layered_File:
        if currentColour in allowedColours and currentColour not in excludedColours:
            lastPixelFound = currentColour
            return True
        return False

    #if lastPixelFound == currentColour:
    if currentColour in allowedColours:
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
    pattern_file = os.path.join(PATTERNS, "{}.png".format(pattern_name))
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
# Create the Master Material File
#
def CreateMasterMaterialFile(filename):
    try:
        with open(filename,'w') as fp_mtl:
            fp_mtl.write("# Created with PNG2OBJ.PY (C) Jason Brooks\n")
            fp_mtl.write("# See www.muckypaws.com\n")
            fp_mtl.write("# https://github.com/muckypaws/PNG2OBJ\n\n")
            fp_mtl.flush()
            fp_mtl.close()
    except Exception as error:
        print(f"Failed to create Material File: {filename}")
        print(f"Error: {error}")
        exit(0)

#
# Finalise the MTL File
#
def FinaliseMasterMaterialFile(filename):
    global mtl_colour_dict
    global CREATE_MTL_FILE
    try:
        with open(filename,'a') as fp_mtl:
            fp_mtl.write(f"#\n# Total Material Colours Created: {len(mtl_colour_dict)}\n#\n")
            fp_mtl.flush()
            fp_mtl.close()
            # Switch off flag as MTL File has been created and finalised.
            CREATE_MTL_FILE = False
    except Exception as error:
        print(f"Failed to append to Material File: {filename}")
        exit(0)
                    
#
# Default Logging Code
#
def log(msg):
    sys.stdout.write("\n")
    sys.stdout.write(str(datetime.now()))
    sys.stdout.write(": ")
    sys.stdout.write(msg)
    sys.stdout.write("\n")
    sys.stdout.flush()


#
# The actual start of Python Code.
#
if __name__ == "__main__":
    # Add user options to the code
    parser = argparse.ArgumentParser(description="Convert PNG Images to OBJ",
                                     epilog='https://github.com/muckypaws/PNG2OBJ')
    #group  = parser.add_mutually_exclusive_group()
    parser.add_argument("-j","--joints", help="Create small joining blocks where cubes are only attached via their corners", action="store_true", default=False)
    parser.add_argument("-m","--mtl",help="Create a Material File with the OBJECT", action="store_true", default=False)
    parser.add_argument("-lc","--listColours",help="List the colours discovered and quantity of pixels",action="store_true")
    parser.add_argument("filename",help="Include the PNG File to convert without the PNG Extension, i.e. art.png just pass art")
    parser.add_argument("-el","--excludelist",nargs="*",type=str, default=[])
    parser.add_argument("-ac","--alphacutoff",help="Cutoff Value for Alpha Byte (0-255), anything equal or below will be treated as fully transparent, above will be treated as fully opaque",type=int,default=254)
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
    
    # First Mutually Excluded Group of Flags
    group=parser.add_mutually_exclusive_group()
    group.add_argument("-fl","--flat",help="Create a Single OBJ File with all colour information",action="store_true", default=True)
    group.add_argument("--layered",help="Create a Multi Layer Set of files for each colour code",action="store_true",default=False)
    group.add_argument("--tower",help="Create a single layer, different heights based on colour order",action="store_true",default=False)
    # Get arguments from the Command Line
    args=parser.parse_args()

    # Check for Jointer Cubes required.
    if args.joints:
        JOINTS_REQUIRED = True

    # Check if We're creating the Material File.
    if args.mtl:
        CREATE_MTL_FILE = True

    if args.flat:
        Create_Layered_File = False
    
    if args.layered:
        Create_Layered_File = True

    if args.tower:
        Create_Towered_File = True 

    ALPHACUTOFF = args.alphacutoff

    Sort_Colours_Flag = args.sort

    Primitive_Multiplier_Background = args.backgroundheight
    Primitive_Multiplier_Layers = args.layermultiplier

    # Ensure we're sorting if only one of the sort flags provided.
    if args.reversesort:
        Sort_Colours_Flag=True

    WORKING_FILENAME = args.filename
    mtl_filename = os.path.join(PATTERNS, "{}.mtl".format(WORKING_FILENAME))

    # Create the Material File if required.
    if args.mtl:
        CreateMasterMaterialFile(mtl_filename)

    if args.excludelist:
        print(f"Excluding the following colours: {args.excludelist}\n")
        Colour_Exclusion_List = args.excludelist

    if args.processcolours:
        print(f"Only Processing the following colours: {args.processcolours}")
        Colour_Process_Only_list = args.processcolours

    Debug_Txt_File = args.debug

    Pixel_W = args.spriteWidth
    Pixel_H = args.spriteHeight


    ColoursOnSingleLayerHeight = args.nextlayeronly

    # Attempt to Load the PNG to memory.
    if loadPNGToMemory() == False:
        print(f"Unable to open file: {WORKING_FILENAME}")
        exit (0)

    print("")
    print(f"    Image Information :")
    print("    -------------------\n")
    print(f"           Image File : {WORKING_FILENAME}")
    print(f"       PNG Image Size : {pattern_w}px (width), {pattern_h}px (height)")
    print(f"   Number of Channels : {channels}")
    print("")
    print(f"     Joints Requested : {JOINTS_REQUIRED}\n Create Material File : {CREATE_MTL_FILE}")
    print(f" Reverse Sort Colours : {Sort_Colours_Flag}")
    print(f"Create Flat File Only : {not Create_Layered_File}" )
    print(f"         Alpha Cutoff : {ALPHACUTOFF}")
    print(f"Background Multiplier : {Primitive_Multiplier_Background:.2f}")
    print(f"     Layer Multiplier : {Primitive_Multiplier_Layers:.2f}")

    if Pixel_W != DEFAULT_PIXEL_WIDTH:
        print(f"   Sprite Sheet Width : {Pixel_W}")
    if Pixel_H != DEFAULT_PIXEL_HEIGHT:    
        print(f"  Sprite Sheet Height : {Pixel_H}")

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
        if args.initialLayerDepth != 0.0 and len(Colour_Process_Only_list) > 1:
            # Set height of initial layer depth
            Primitive_Layer_Depth = args.initialLayerDepth
            Primitive_Initial_Layer_Depth = (args.maxdepth - args.initialLayerDepth) / (len(Colour_Process_Only_list) - 1)
        else:
            if Colour_Process_Only_list.count:
                Primitive_Layer_Depth = args.maxdepth / len(Colour_Process_Only_list)
    else: 
        Primitive_Layer_Depth = abs(Primitive_Multipler*CUBE_Y)

    print(f" Object Max Depth (Z) : {args.maxdepth:.2f}mm")
    if Primitive_Initial_Layer_Depth != 0.0:
        print(f"      First Layer Depth : {Primitive_Layer_Depth:.2f}mm")
        print(f"      Next Layer Depths : {Primitive_Initial_Layer_Depth:.2f}mm")
        
    else:
        print(f"     Each Layer Depth : {Primitive_Layer_Depth:.2f}mm")
    print(f"     Requested Layers : {len(Colour_Process_Only_list)}")
    

    if pattern_w != Image_Real_Width or pattern_h != Image_Real_Height:
        print(f"\n   Actual Image Width : {Image_Real_Width} Pixels")
        print(f"  Actual Image Height : {Image_Real_Height} Pixels")
        print(f"        Image Start X : {Image_MinX}")
        print(f"        Image Start Y : {Image_MinY}")
        print(f"         Bounding Box : ({Image_MinX},{Image_MinY},{Image_MaxX},{Image_MaxY}) ")

    print(f"     Background Frame : {not args.noframe}")
    if Image_Real_Height < 1 or Image_Real_Width < 1:
        print(f"No Image Data to Process, Quitting...")
        exit(0)

    print(f"\n  Object Width/Height : {widthMultiplier:.2f}mm x {heightMultiplier:.2f}mm")

    if Debug_Txt_File:
        print(f"\n      Debug Text File : {Debug_Txt_File}\n")

    if ColoursOnSingleLayerHeight:
        print(f"\n **** Seperate Colours On Single Layer Selected ****")

    if len(Colour_Exclusion_List) > 0:
        print(f"\nColour list to exclude: {Colour_Exclusion_List}")
    if len(Colour_Process_Only_list) > 0:
        print(f"\n   Colours to process : {Colour_Process_Only_list}")

    print("\n")

    #displayColourInformation()

    if args.listColours:
        displayColourInformation()
    else:
        main(args.noframe)

