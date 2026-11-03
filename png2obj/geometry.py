"""Primitive geometry: cube / joint vertex, normal and face tables, plus the
vertex-selection helper. Extracted verbatim from PNG2ObjV3.py (Phase 1)."""


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



# Update Verticies depending on position (0 or non 0)
# Currently Assumes, 0 - Left, non-Zero right
#
def update_vert(val, r1, r2):
    """
    Select one of two values based on whether the input is zero or positive.

    This is a simple conditional utility typically used to determine which X or Y
    coordinate to use depending on a directional sign or polarity.

    Args:
        val (float): A directional or comparative value (usually a delta or sign).
        r1 (Any): Value returned when val is 0 or negative.
        r2 (Any): Value returned when val is positive.

    Returns:
        Any: r2 if val > 0.0, else r1.

    TODO:
        - Rename function to clarify purpose (e.g. select_by_sign, pick_side_based_on_direction)
    """
    if val > 0.0:
        return r2
    return r1
