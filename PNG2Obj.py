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
# V1.00 - 3rd June 2022 - The Platty Joobs Edition ;)
# V1.01 - 5th June 2022 - The Platty Pudding Edition ;)
#                         Add Jointer Cubes for diagonal pixels without support
#                         Only needed if you're using a printer.
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

import os
import sys
import png
from datetime import datetime

# Application Defaults

# Default location for File
PATTERNS = "./"

# Set Pixel Width and Height if Sprites are fixed width within the sheet, otherwise 
# use a high number.
Pixel_W = 1024
Pixel_H = 1024

# X is positive, Y is negative unless you want to flip the image.
CUBE_X = 10
CUBE_Y = -10

# Define the Alpha Value as Cut Off For the Pixel
ALPHACUTOFF = 200

# Define TRUE if Printing, FALSE if anything else as not required
JOINTS_REQUIRED = True

# Used to define the Current Face Counter
# Needed to ensure Vertices are correctly defined.
Current_Face = 0

# Basic Definition of cube with 24 Vertices (4 Sets of Co-Ords per face)
cube_vertices = (   [  0.000000, 10.000000, 10.000000],
                    [ 10.000000, 10.000000, 10.000000],
                    [ 10.000000, 10.000000,  0.000000],
                    [  0.000000, 10.000000,  0.000000],
                    [ 10.000000, 10.000000, 10.000000],
                    [ 10.000000,  0.000000, 10.000000],
                    [ 10.000000,  0.000000,  0.000000],
                    [ 10.000000, 10.000000,  0.000000],
                    [ 10.000000,  0.000000, 10.000000],
                    [  0.000000,  0.000000, 10.000000],
                    [  0.000000,  0.000000,  0.000000],
                    [ 10.000000,  0.000000,  0.000000],
                    [  0.000000,  0.000000, 10.000000],
                    [  0.000000, 10.000000, 10.000000],
                    [  0.000000, 10.000000,  0.000000],
                    [  0.000000,  0.000000,  0.000000],
                    [ 10.000000, 10.000000, 10.000000],
                    [  0.000000, 10.000000, 10.000000],
                    [  0.000000,  0.000000, 10.000000],
                    [ 10.000000,  0.000000, 10.000000],
                    [  0.000000,  0.000000,  0.000000],
                    [  0.000000, 10.000000,  0.000000],
                    [ 10.000000, 10.000000,  0.000000],
                    [ 10.000000,  0.000000,  0.000000])

#Basic Definition of a Primitives connecting faces 
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
                [21, 23, 24])


# Basic Definition for a Jointer Cube Where Pixels are connected by Corners Only
# This is needed if there's no overlap on your printer and want to ensure a 
# a connection that should lift off the printer.

joint_verticies = ( [  7.171573,  0.000000, 7.000000],
                    [ 10.000000,  2.828427, 7.000000],
                    [ 10.000000,  2.828427, 3.000000],
                    [  7.171573,  0.000000, 3.000000],
                    [ 10.000000,  2.828427, 7.000000],
                    [ 12.828427, -0.000000, 7.000000],
                    [ 12.828427, -0.000000, 3.000000],
                    [ 10.000000,  2.828427, 3.000000],
                    [ 12.828427, -0.000000, 7.000000],
                    [ 10.000000, -2.828427, 7.000000],
                    [ 10.000000, -2.828427, 3.000000],
                    [ 12.828427, -0.000000, 3.000000],
                    [ 10.000000, -2.828427, 7.000000],
                    [  7.171573,  0.000000, 7.000000],
                    [  7.171573,  0.000000, 3.000000],
                    [ 10.000000, -2.828427, 3.000000],
                    [ 10.000000,  2.828427, 7.000000],
                    [  7.171573,  0.000000, 7.000000],
                    [ 10.000000, -2.828427, 7.000000],
                    [ 12.828427, -0.000000, 7.000000],
                    [ 10.000000, -2.828427, 3.000000],
                    [  7.171573,  0.000000, 3.000000],
                    [ 10.000000,  2.828427, 3.000000],
                    [ 12.828427, -0.000000, 3.000000])

joint_faces = ( [  1,  2,  4],
                [  4,  2,  3],
                [  5,  6,  8],
                [  8,  6,  7],
                [  9, 10, 12],
                [ 12, 10, 11],
                [ 13, 14, 16],
                [ 16, 14, 15],
                [ 17, 18, 20],
                [ 20, 18, 19],
                [ 21, 22, 24],
                [ 24, 22, 23])

# Update Verticies depending on position (0 or non 0)
def update_vert(val,r1,r2):
    if val > 0.0:
        return r2
    return r1

#
# Create a Primitive, in this example a Cube, but could be swapped for 
#   Any primitive type
#
def create_primitive(primitive_x, primitive_y, width, primitive_vert, primitive_face, jointFlag):
    global Current_Face

    strVertices = f"o Pixel_{primitive_x}_{primitive_y}\n"
    strFaces = ""

    # Get the number of entries for Cube Vertices
    # For future where primitive may change
    vert_len = len(primitive_vert)
    face_len = len(primitive_face)

    rx = primitive_x * CUBE_X
    ry = primitive_y * CUBE_Y
    rx2 = rx + (CUBE_X * width)
    ry2 = ry + CUBE_Y

    myFormatter = "{0:.6f}"

    #
    # Generate the Basic Primitive for the Model
    #
    for index in range(vert_len):
        v1 = primitive_vert[index][0]
        v2 = primitive_vert[index][1]
        v3 = primitive_vert[index][2]

        # Yeah, quick and dirty, I need to think this through
        if not jointFlag:
            v1 = update_vert(v1, rx, rx2)
            v2 = update_vert(v2, ry, ry2)
        else:
            v1 = v1 + rx
            v2 = v2 + ry

        strVertices = strVertices + "v " + str(myFormatter.format(v1)) + " " + str(myFormatter.format(v2)) + " " + str(myFormatter.format(v3)) + "\n"

    strVertices = strVertices + "# "+str(vert_len)+f" Vertices\ng Extrude_{primitive_x}_{primitive_y}\n"

    for index in range(face_len):
        f1 = primitive_face[index][0] + Current_Face
        f2 = primitive_face[index][1] + Current_Face
        f3 = primitive_face[index][2] + Current_Face

        strFaces = strFaces + "f " + f"{f1} {f2} {f3}\n"

    Primitive_String = strVertices + strFaces + "# "+str(face_len)+" Faces\n\n"

    # update face Index Counter to next set 
    Current_Face = Current_Face + (face_len * 2)

    return Primitive_String

#
# Convert Colour To Pixel - Can extend this to exclude colour ranges in future updates.
#
def getPixelFromRow(x, row, channels, rowWidth):
    # Calculate the offset into the ROW for pixel information
    offset_x = (x * channels) % (rowWidth * channels)
    pixel = 0

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
        if a < ALPHACUTOFF:
            pixel = 0

    return pixel

#
# Process a simple set of rules to determine if a Jointer Block is required.
# That is missing diagonal pixes.  It's crude and needs refinement.
#
def CheckJointRequired(x ,row, nextRow, channels, pattern_w):
    isJointRequired = False

    # Not Checking last pixel as this is covered 
    if x >= (pattern_w-1): 
        return isJointRequired

    a = getPixelFromRow(x,   row,     channels, pattern_w)
    b = getPixelFromRow(x+1, row,     channels, pattern_w)
    c = getPixelFromRow(x,   nextRow, channels, pattern_w)
    d = getPixelFromRow(x+1, nextRow, channels, pattern_w)

    if (a > 0 and d > 0 and b == 0 and c == 0) or (b > 0 and c > 0 and a == 0 and d == 0):
        isJointRequired = True

    return isJointRequired
#
# And this is where all that magic happens.
#   A real Python Programmer can probably optimise this using some Python Magic.
#
def main():
    # Total Number of Primitives Created
    Total_Primitives = 0

    # Define RGB Colours as 0
    r, g, b, a = 0, 0, 0, 255

    # Load the PNG File, Check if Valid
    pattern, pattern_w, pattern_h, pattern_meta = load_pattern(sys.argv[1])
    
    # Check we're dealing with 8 Bits per channel.
    if pattern_meta['planes'] < 3:
        log(f"PNG File Unsupported, convert to 8 Bits per Channel - 24 bit")
        exit(0)

    # Check if We've loaded a Valid PNG File
    if pattern is None:
        log(f"File: {sys.argv[1]} is not a valid PNG File")
        exit(0)

    # Check to see if Alpha Byte Present and set number of channels accordingly
    alpha = pattern_meta['alpha']
    channels = 4 if alpha else 3

    # Define output Filenames based on Input, creating 
    #   an  OBJ file with 3D Mesh Details
    #       TXT file with pixel data as seen
    obj_file = os.path.join(PATTERNS, "{}.obj".format(sys.argv[1]))
    txt_file = os.path.join(PATTERNS, "{}.txt".format(sys.argv[1]))

    # If we're adding Jointer Blocks this will be required.
    LastRow = False

    # open files for Writing, Note we're not checking their presence as we're overwriting/creating
    #   from scratch each time.
    try:
        # TODO: Ass some error checking here, rather than relay on TRY/CATCH Scenarios.
        with open(obj_file,'w') as fp_obj:
            with open(txt_file,'w') as fp_txt:
                # Create Header for OBJ File
                header = "# Creator PNG2OBJ.py - Jason Brooks 2022\n# " + str(datetime.now()) + "\n"
                header = header + f"# Original File: {sys.argv[1]}.png, Width: {pattern_w}, Height: {pattern_h}\n"
                fp_obj.write( header )

                # Set Current Y Position, we're only using this for situations where sprite files
                #   make it difficult to seperate the blocks post conversion, so we add a space
                #   between the primitives on the 3D OBJ File
                start_y = 0

                # Work our way through each row of the PNG File.
                for y in range(pattern_h):
                    row = pattern[int(y % pattern_h)]
                    
                    # Get Next Row for Jointer Block Processing.
                    # We're cheating by MOD by the PNG Height
                    # But will set the Last row flag so we don't 
                    # Process the rules for this.
                    nextRow = pattern[int((y+1) % pattern_h)]

                    fp_txt.write('\n')

                    # Check If We're processing the last row of Pixels
                    if y == (pattern_h-1):
                        LastRow = True

                    # If we're splitting models based on pixel width and height add and extra line
                    #   And ensure we start the next primitive further down to enforce a gap in the model
                    if not(y % Pixel_H):
                        fp_txt.write('\n')
                        start_y = start_y + 1
                    
                    # Iterate through the data with 
                    start_x = 0
                    pixel_found = False
                    primitive_width = 0
                    primitive_x = 0
                    for x in range(pattern_w):
                        # Check if We're Adding extra space between each sprite based
                        #   on fixed pixel width per sprite.
                        if not(x % Pixel_W):
                            fp_txt.write("|")
                            start_x=start_x+1

                            if pixel_found:
                                fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, cube_vertices, cube_faces, newJoint) )
                                pixel_found = False
                                primitive_width = 0
                                Total_Primitives += 1

                        # Get Pixel from Row
                        pixel = getPixelFromRow(x, row, channels, pattern_w)

                        # If Pixel present then add to TXT File and create primitive.
                        if pixel > 0:
                            fp_txt.write("*")
                            if not pixel_found:
                                pixel_found = True
                                primitive_x = start_x

                            # Update Primitive Width
                            primitive_width = primitive_width + 1
                            #fp_obj.write(  create_primitive(start_x, start_y) )
                        else:
                            if pixel_found:
                                fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, cube_vertices, cube_faces, newJoint) )
                                pixel_found = False
                                primitive_width = 0
                                Total_Primitives += 1
                            fp_txt.write(" ")

                        # Check if we're to add Jointer Blocks
                        if JOINTS_REQUIRED and not LastRow:
                            # Check if Blocks meet the Jointer rule
                            newJoint = CheckJointRequired(x,row, nextRow, channels, pattern_w)

                            if newJoint:
                                fp_obj.write(  create_primitive(start_x, start_y + 1, 1, joint_verticies, joint_faces, newJoint) )
                                newJoint = False



                        # Update X Position (Taking into account an offset if we're adding space between sprites)
                        start_x = start_x + 1

                    # Update to the next Y Postion and check if we have an unwritted primitive to complete
                    if pixel_found:
                        fp_obj.write( create_primitive(primitive_x, start_y, primitive_width, cube_vertices, cube_faces, newJoint) )
                        pixel_found = False
                        primitive_width = 0
                        primitive_x = 0
                        Total_Primitives += 1

                    start_y = start_y + 1

                # Write and Flush the Object File
                fp_obj.write(f"#\n# Total Primitives Created: {Total_Primitives}\n#\n")
                fp_obj.flush()
                fp_obj.close()

                # Write and Flush the TXY File
                fp_txt.write('\n')
                fp_txt.flush()
                fp_txt.close()

    except:
        # Bad Practice I know...
        print("Failed to write file: ",obj_file)


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
# Default Logging Code
#
def log(msg):
    sys.stdout.write(str(datetime.now()))
    sys.stdout.write(": ")
    sys.stdout.write(msg)
    sys.stdout.write("\n")
    sys.stdout.flush()


#
# The actual start of Python Code.
#
if __name__ == "__main__":
    if(len(sys.argv) > 1):
        print (sys.argv[1])
    else:
        print (len(sys.argv))
        print("\nProvide PNG Filename to convert")
        exit(0)
    
    main()
