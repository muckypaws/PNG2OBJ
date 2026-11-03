"""Low-level SVG element builders and raster helpers (circles, arrays).

These functions are pure: they take all inputs as arguments and return strings
or mutate a passed-in array, with no module-global state. Extracted verbatim
from PNG2ObjV3.py (Phase 1)."""



#
# Create an Array we use for the Optical Illusion Data
#
def create_array(size :int):
    """
    Create a square 2D array (size x size) filled with space characters.

    Args:
        size (int): The number of rows and columns for the square array.

    Returns:
        list[list[str]]: A 2D array (list of lists) filled with ' ' (space) characters.
    """
    return [[' ' for _ in range(size)] for _ in range(size)]



#
# Plot Circle Points based on each quadrant and opposite faces.
#
def plot_circle_points(array, cx, cy, x, y):
    """
    Plot a symmetrical set of 8 points around the center (cx, cy) to form part of a circle.

    This function uses Bresenham's symmetry to mark pixels on all eight octants,
    updating the given 2D character array in-place.

    Args:
        array (list[list[str]]): The 2D drawing canvas.
        cx (int): X-coordinate of the circle center.
        cy (int): Y-coordinate of the circle center.
        x (int): Offset from center along the X-axis.
        y (int): Offset from center along the Y-axis.

    Returns:
        None. Modifies the array in-place.
    """
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
    """
    Draw a full circle on a 2D character array using Bresenham's circle algorithm.

    Args:
        array (list[list[str]]): The 2D canvas to draw the circle on (modified in-place).
        center_x (int): X-coordinate of the circle's center.
        center_y (int): Y-coordinate of the circle's center.
        radius (int): Radius of the circle in array units.

    Returns:
        None. Modifies the array in-place by plotting '*' at appropriate points.
    """
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



#    print_array(SVG_ILLUSION_ARRAY)


#
# Debugging purposes to see the array...
#
def print_array(array):
    """
    Print a 2D character array row by row as a visual grid.

    Args:
        array (list[list[str]]): The array to print. Each sublist represents a row.

    Returns:
        None. Output is sent directly to standard output.
    """
    for row in array:
        print(''.join(row))



#
# Add Centred Text
#
# TODO: Make font-size and stroke-width configurable parameters
# TODO: Consider accepting a style dict or class for future flexibility
def add_svg_centeredText(x, y, text, fill_colour):
    """
    Generate a centered SVG <text> element with stroke-based outlining.

    Args:
        x (float): The x-coordinate in mm for the text anchor point.
        y (float): The y-coordinate in mm for the text anchor point.
        text (str): The text content to display.
        fill_colour (str): Stroke colour for the text outline (e.g. "#000000").

    Returns:
        str: A formatted SVG <text> tag with positioning, alignment, and stroke styling.
    """
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
    """
    Generate an SVG <circle> element centered at (x, y) with optional stroke and fill.

    Args:
        x (float): X-coordinate of the circle center in mm.
        y (float): Y-coordinate of the circle center in mm.
        radius (float, optional): Radius of the circle in mm. Default is 5.0.
        fill_colour (str, optional): Fill colour of the circle (e.g. "#FF0000").
        stroke_width (float, optional): Width of the stroke in mm. If 0.0, stroke is omitted.
        stroke (str, optional): Stroke colour. Ignored if stroke_width is 0.

    Returns:
        str: A formatted SVG <circle> tag.
    
    TODO:
        - Consider adding support for additional SVG attributes via kwargs or a style object.
        - Optionally validate inputs to prevent invalid SVG formatting.
    """
    circle_str = (f'\t\t<circle cx="{x:.3f}mm" cy="{y:.3f}mm" r="{radius:.3f}mm" fill="{fill_colour}" ')
    if stroke_width != 0.0:
        circle_str += f'stroke="{stroke}" stroke-width="{stroke_width}mm" '


    return circle_str + "/> \n"



#
# Add rectangle
#
def add_svg_rectangle(id, x, y, width, height, rx=0.0, ry=0.0, fill_colour="#000000", opacity = 100.0, stroke_width = 0.0, stroke_colour = "#000000"):
    """
    Generate an SVG <rect> element with optional rounded corners, fill, and stroke.

    Args:
        id (str): Optional ID to assign to the rect.
        x (float): X-position of the rectangle's top-left corner in mm.
        y (float): Y-position of the rectangle's top-left corner in mm.
        width (float): Width of the rectangle in mm.
        height (float): Height of the rectangle in mm.
        rx (float): Optional rounding percentage for x-radius (0–100).
        ry (float): Optional rounding percentage for y-radius (0–100).
        fill_colour (str): Fill colour in hex or named format.
        opacity (float): Fill opacity as a percentage (0–100).
        stroke_width (float): Stroke width in mm. 0 disables stroke.
        stroke_colour (str): Stroke colour.

    Returns:
        str: SVG-compliant <rect> string with given attributes.
    
    TODO:
        - Allow setting stroke opacity separately.
        - Extract style string to helper/template function.
        - Re-enable canvas dimension tracking when refactoring.
    """    # Base rectangle attributes
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
