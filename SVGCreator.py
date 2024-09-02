#!/usr/bin/env python3

import sys
import datetime
import random

SVG_HEADER  = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'

#
# Create and Write an SVG Object to File with the Square Optical Illusion.
#
def create_svg(filename, width, height, rect_width=20.0, rect_height=20.0, rect_radius_x = "25%", rect_radius_y = "25%"):
    try:
        with open(filename, 'w') as fp:
            # Write the Header
            fp.write(SVG_HEADER)
            # Write the Drawings Dimensions
            fp.write(f'<svg width="{rect_width * width}mm" height="{rect_height * height}mm" xmlns="http://www.w3.org/2000/svg">\n')

            # Loop Counter to ensure we get all diagonals.
            max_range = width + height + 1
            
			# Main Optical Illusion Drawing Group
            fill_group = [f'\t<g id="OpticalIllusionGroup">\n']
            
			half_rect_width = rect_width / 2
            half_rect_height = rect_height / 2

			# Loop Across the Object
            for x in range(max_range):
                # The Start Y Position will typically be Zero, when it moves to the right of the Width, 
                # We start offseting the Y position on Grid to be max Width, Y = 0 -> HEIGHT
                # Just a trick without additional loops.
                # range_x is fixed to all columns up to maximum column width
                start_y = max(0, x - width)
                range_x = min(x, width)
                
				# Label up each of the Diagonal Groups with their start X,Y Coords
                # Diagonals set from Top Right to Bottom Left
                fill_group.append(f'\t\t<g id="DiagonalGroup{range_x}:{start_y}">\n')

				# Lets do the work.
                for xpos in range(range_x, -1, -1):
                    # Check if we're in range of the grid.
                    if xpos <= width and start_y <= height:
                        # Set a random Colour
                        rand = random.randint(0, 10)
                        fill_color = (
                            "#000000" if rand <= 3 else
                            "#008040" if rand <= 5 else
                            "#00ff80" if rand <= 7 else
                            "#ffffff"
                        )
                        rect_x = xpos * rect_width - half_rect_width
                        rect_y = start_y * rect_height - half_rect_height
                        fill_group.append(
                            f'\t\t\t<rect width="{rect_width}mm" height="{rect_height}mm" '
                            f'x="{rect_x}mm" y="{rect_y}mm" fill="{fill_color}" />\n'
                        )
                        start_y += 1

                fill_group.append('\t\t</g>\n')

            fill_group.append('\t</g>\n')
            fp.write(''.join(fill_group))

            # Dark and Light Groups
            dark_group = [f'\t<g id="DarkGroup">\n']
            light_group = [f'\t<g id="LightGroup">\n']

            for y in range(height):
                current_y = y * 20.0
                for x in range(width):
                    current_x = x * 20.0
                    fill_color = "#008040" if (x % 2) == (y % 2) else "#00ff80"
                    group = dark_group if fill_color == "#008040" else light_group
                    group.append(
                        f'\t\t<rect width="{rect_width}mm" height="{rect_height}mm" '
                        f'x="{current_x}mm" y="{current_y}mm" '
                        f'rx="{rect_radius_x}" ry="{rect_radius_y}" fill="{fill_color}" />\n'
                    )

            dark_group.append("\t</g>\n")
            light_group.append("\t</g>\n")

            # Write Dark and Light Groups
            fp.write(''.join(dark_group))
            fp.write(''.join(light_group))

            # Finalize SVG
            fp.write('</svg>\n')

    except IOError as error:
        print(f"File error: {error}")
    except Exception as error:
        print(f"Unexpected error: {error}")

#
# Default Logging Code
#
def log(msg):
    sys.stdout.write(f"\n{datetime.datetime.now()}: {msg}\n")
    sys.stdout.flush()

#
# The actual start of Python Code.
#
if __name__ == "__main__":
    if(len(sys.argv) > 1):
        print (sys.argv[1])
        #CreateSVG(sys.argv[1], 30, 20)
        create_svg("Test.svg", 20, 20)
    else:
        print (len(sys.argv))
        print("\nan SVG Filename if required.")
        exit(0)