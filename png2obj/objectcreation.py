"""3D object creation: OBJ primitive assembly, colour/layer processing, and the
parametric surface generators.

Builds Wavefront OBJ geometry from the loaded image (flat / layered / towered),
applies optional printing joints, writes the material file, and drives the
experimental parametric designs. Shared state and tuning come from
png2obj.runtime.
"""
import math
import os
import sys
from datetime import datetime
from pathlib import Path

from png2obj import runtime
from png2obj.geometry import (
    cube_vertices, cube_normals, cube_faces,
    joint_verticies, joint_normals, joint_faces, update_vert,
)
from png2obj.imageprocessing import getPixelFromRow, CheckJointRequired



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

        strVertices = strVertices + f"v {v1:.6f} {v2:.6f} {v3:.6f}\n"

    strVertices = strVertices + "# "+str(vert_len)+f" Vertices\n"

    strNormals = ""
    # Bit of a Bodge... 
    for index in range(len(primitive_normals)):
        n1 = primitive_normals[index][0]
        n2 = primitive_normals[index][1]
        n3 = primitive_normals[index][2]
        strNormals = strNormals + f"vn {n1:.6f} {n2:.6f} {n3:.6f}\n"

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

    # Layered mode tags every primitive with one fixed material index. colourMatch
    # is constant for this call and the colour set is stable here, so resolve the
    # index once instead of rebuilding a key list per primitive.
    layered_colour_index = (
        list(runtime.MATERIALS.colours).index(colourMatch)
        if runtime.Create_Layered_File else None
    )

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
                                thisColour = layered_colour_index
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
                                        thisColour = layered_colour_index
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
                                thisColour = layered_colour_index
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
                        thisColour = layered_colour_index
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
