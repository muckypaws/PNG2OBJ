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
# V1.02 - 28th June 2022- Over the Rainbow Edition
#                         Added Option to Add Material File for Coloured Pixels
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

#from glob import glob
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


pattern = 0
pattern_w = 0
pattern_h = 0
pattern_meta = 0
channels = 0

# X is positive, Y is negative unless you want to flip the image.
CUBE_X = 10
CUBE_Y = -10

# Define the Alpha Value as Cut Off For the Pixel
ALPHACUTOFF = 254

# Define TRUE if Printing, FALSE if anything else as not required
JOINTS_REQUIRED = False

# Define TRUE if a corresponding MTL File is to be created for Colour Cubes
CREATE_MTL_FILE = False

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

#
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
mtl_colour_dict   = {"#000000":0}
mtl_current_index = 1
mtl_filename = ""
mtl_lib_filename = ""

# Update Verticies depending on position (0 or non 0)
def update_vert(val,r1,r2):
    if val > 0.0:
        return r2
    return r1

#
# Create a Primitive, in this example a Cube, but could be swapped for 
#   Any primitive type
#
def create_primitive(primitive_x, primitive_y, width, height, primitive_vert, primitive_face, jointFlag, material_index):
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
    ry2 = ry + (CUBE_Y * height)

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

    strVertices = strVertices + "# "+str(vert_len)+f" Vertices\ng Pixel_{primitive_x}_{primitive_y}_F\n"

    if CREATE_MTL_FILE:
        strVertices += "mtllib "+os.path.basename(mtl_filename) + "\n" + \
            f"usemtl {material_index}\n"

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
    ColourCode = "#000000"


    # Need the current Index of Colour or do we? Could use dict len?
    global mtl_current_index

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
            r = 0
            g = 0
            b = 0

    # Check to see if we already have this material.
    ColourCode = "#"+'{:02x}'.format(r)+'{:02x}'.format(g)+'{:02x}'.format(b)

    if pixel > 0:
        if not ColourCode in mtl_colour_dict:
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
    if pixel:
        material_index = mtl_colour_dict[ColourCode]
        mtl_colour_dict[ColourCode] += 1

    return pixel, material_index, ColourCode

#
# Process a simple set of rules to determine if a Jointer Block is required.
# That is missing diagonal pixes.  It's crude and needs refinement.
#
def CheckJointRequired(x ,row, nextRow, channels, pattern_w):
    isJointRequired = False

    # Not Checking last pixel as this is covered 
    if x >= (pattern_w-1): 
        return isJointRequired

    a, mi, mm = getPixelFromRow(x,   row,     channels, pattern_w)
    b, mi, mm = getPixelFromRow(x+1, row,     channels, pattern_w)
    c, mi, mm = getPixelFromRow(x,   nextRow, channels, pattern_w)
    d, mi, mm = getPixelFromRow(x+1, nextRow, channels, pattern_w)

    if (a > 0 and d > 0 and b == 0 and c == 0) or (b > 0 and c > 0 and a == 0 and d == 0):
        isJointRequired = True

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
def main():
    # Reset the file counter, though should be zero on start up
    # Used for debugging purposes.

    fileCounter = 0

    # Load the PNG to memory if possible.
    if loadPNGToMemory() == False:
        print(f"Unable to process file: {sys.argv[1]}")
        exit (0)

    # Calculate the Different Coloured Pixels
    discoverPixelLayers()

    # Create the Background Object File 
    # Flat Structure width and height of PNG Image.
    obj_file = os.path.join(PATTERNS, "{}.obj".format(sys.argv[1]))
    try:
        # TODO: Add some error checking here, rather than rely on TRY/CATCH Scenarios.
        with open(obj_file,'w') as fp_obj:
            fp_obj.write(create_primitive(0, 0, pattern_w, pattern_h, cube_vertices, joint_faces, 0, 0))
            fp_obj.flush()
            fp_obj.close()
    except:
    # Bad Practice I know...
       print("Failed to write Initial file: ",obj_file)
       exit(0)


    SortedColours = {key: val for key, val in sorted(mtl_colour_dict.items(), key = lambda ele: ele[0], reverse=True)}
    
    # Remove Background Colour of 000000 
    del SortedColours["#000000"]

    print("Layer Order:")
    for nextLayer in SortedColours:
        print(f"{nextLayer}")

    print(f"Found : {len(mtl_colour_dict)} Colours")

    while len(SortedColours) > 0:
        nextLayer = list(SortedColours.keys())[0]
        print(f"Processing Colour: {nextLayer}")
        resp = processFile(nextLayer, SortedColours)
        if resp == False:
            print("Failed to process file:")
            exit (0)
        del SortedColours[nextLayer]



def loadPNGToMemory():
    # Load the PNG File, Check if Valid
    global pattern, pattern_w, pattern_h, pattern_meta, channels

    pattern, pattern_w, pattern_h, pattern_meta = load_pattern(sys.argv[1])

    # If File Wasn't Found Time to Quit
    if pattern == None:
        return False
    
    # Check we're dealing with 8 Bits per channel.
    if pattern_meta['planes'] < 3:
        log(f"PNG File Unsupported, convert to 8 Bits per Channel - 24 bit")
        return False

    # Check if We've loaded a Valid PNG File
    if pattern is None:
        log(f"File: {sys.argv[1]} is not a valid PNG File")
        return False

    # Check to see if Alpha Byte Present and set number of channels accordingly
    alpha = pattern_meta['alpha']
    channels = 4 if alpha else 3

    return True

# Work out the number of colours in the PNG
def discoverPixelLayers():
    # Work our way through each row of the PNG File.
    for y in range(pattern_h):
        row = pattern[int(y % pattern_h)]

        for x in range(pattern_w):
            # Get Pixel from Row
            getPixelFromRow(x, row, channels, pattern_w)

    
def processFile(colourMatch, allowedDictionary):
    CUBE_X = 10
    CUBE_Y = -10

    # Used to define the Current Face Counter
    # Needed to ensure Vertices are correctly defined.
    global Current_Face
    Current_Face = 0
    # Total Number of Primitives Created
    Total_Primitives = 0

    # Define RGB Colours as 0
    r, g, b, a = 0, 0, 0, 255

    global mtl_filename

    # Define output Filenames based on Input, creating 
    #   an  OBJ file with 3D Mesh Details
    #       TXT file with pixel data as seen
    obj_file = os.path.join(PATTERNS, "{}{}.obj".format(sys.argv[1],str(colourMatch)))
    txt_file = os.path.join(PATTERNS, "{}{}.txt".format(sys.argv[1],str(colourMatch)))
    mtl_filename = os.path.join(PATTERNS, "{}{}.mtl".format(sys.argv[1],str(colourMatch)))

    # If we're adding Jointer Blocks this will be required.
    LastRow = False

    # open files for Writing, Note we're not checking their presence as we're overwriting/creating
    #   from scratch each time.
    try:
        # TODO: Add some error checking here, rather than relay on TRY/CATCH Scenarios.
        with open(obj_file,'w') as fp_obj:
            with open(txt_file,'w') as fp_txt:
                # Create Header for OBJ File
                header = "# Creator PNG2OBJ.py - © Jason Brooks 2022\n# " + str(datetime.now()) + "\n"
                header = header + f"# Original File: {sys.argv[1]}.png, Width: {pattern_w}, Height: {pattern_h}\n"
                fp_obj.write( header )

                if CREATE_MTL_FILE:
                    with open(mtl_filename,'w') as fp_mtl:
                        fp_mtl.write("# Created with PNG2OBJ.PY (C) Jason Brooks\n")
                        fp_mtl.write("# See www.muckypaws.com\n")
                        fp_mtl.write("# https://github.com/muckypaws/PNG2OBJ\n\n")
                        fp_mtl.flush()
                        fp_mtl.close()


                # Set Current Y Position, we're only using this for situations where sprite files
                #   make it difficult to seperate the blocks post conversion, so we add a space
                #   between the primitives on the 3D OBJ File
                start_y = 0

                # Create Top Corner for Alignment
                #fp_obj.write(  create_primitive(-1, -1, 1, 1, cube_vertices, cube_faces, False , 0) )

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
                    pixel_found_colour_index = 0
                    primitive_width = 0
                    primitive_x = 0

                    for x in range(pattern_w):
                        # Check if We're Adding extra space between each sprite based
                        #   on fixed pixel width per sprite.
                        if not(x % Pixel_W):
                            fp_txt.write("|")
                            start_x=start_x+1

                            #if pixel_found:
                                #fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, cube_vertices, cube_faces, False, pixel_found_colour_index) )
                            #    pixel_found = False
                            #    primitive_width = 0
                             #   pixel_found_colour_index = 0
                            #    Total_Primitives += 1

                        # Get Pixel from Row
                        pixel,mi, mm = getPixelFromRow(x, row, channels, pattern_w)

                        # If Pixel present then add to TXT File and create primitive.
                        #if pixel > 0 and mi==colourIndex:
                        #if mi==colourIndex:
                        if mm in allowedDictionary:
                            fp_txt.write("*")
                            if not pixel_found:
                                pixel_found = True
                                primitive_x = start_x
                                pixel_found_colour_index = mi
                            else:
                                # Check we're on the same colour
                                #if mi != pixel_found_colour_index:
                                if mm not in allowedDictionary:
                                    fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False , pixel_found_colour_index) )
                                    primitive_width = 0
                                    Total_Primitives += 1
                                    pixel_found_colour_index = mi
                                    primitive_x = start_x

                            # Update Primitive Width
                            primitive_width = primitive_width + 1
                            #fp_obj.write(  create_primitive(start_x, start_y) )
                        else:
                            if pixel_found:
                                fp_obj.write(  create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False , pixel_found_colour_index) )
                                pixel_found = False
                                primitive_width = 0
                                Total_Primitives += 1
                            fp_txt.write(" ")

                        # Check if we're to add Jointer Blocks
                        if JOINTS_REQUIRED and not LastRow:
                            # Check if Blocks meet the Jointer rule
                            newJoint = CheckJointRequired(x,row, nextRow, channels, pattern_w)

                            if newJoint:
                                fp_obj.write(  create_primitive(start_x, start_y + 1, 1, 1, joint_verticies, joint_faces, newJoint, mi) )
                                newJoint = False



                        # Update X Position (Taking into account an offset if we're adding space between sprites)
                        start_x = start_x + 1

                    # Update to the next Y Postion and check if we have an unwritten primitive to complete
                    if pixel_found:
                        fp_obj.write( create_primitive(primitive_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False, pixel_found_colour_index) )
                        pixel_found = False
                        primitive_width = 0
                        primitive_x = 0
                        Total_Primitives += 1

                    start_y = start_y + 1

                # Write and Flush the Object File
                fp_obj.write(  create_primitive(start_x, start_y, primitive_width, 1, cube_vertices, cube_faces, False , 0) )

                fp_obj.write(f"#\n# Total Primitives Created: {Total_Primitives}\n#\n")
                if CREATE_MTL_FILE:
                    fp_obj.write(f"#\n# Total Material Colours Created: {len(mtl_colour_dict)-1}\n#\n")
                fp_obj.flush()
                fp_obj.close()

                # Write and Flush the TXT File
                fp_txt.write('\n')
                fp_txt.flush()
                fp_txt.close()

    except:
    # Bad Practice I know...
       print("Failed to write file: ",obj_file)
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
    if(len(sys.argv) > 1):
        print (sys.argv[1])
    else:
        print (len(sys.argv))
        print("\nProvide PNG Filename to convert")
        exit(0)
    
    main()
