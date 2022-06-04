# PNG2OBJ
Convert Simple PNG Files to Wavefront OBJ Files for programs that support OBJ Import, CAD, zBrush etc

Created by Jason Brooks: www.muckypaws.com and www.wonkypix.com
           3rd June 2022

This simple code takes a 3 Channel PNG File and converts any colour pixel found to a primitive
It will search along the X-Axis to combine primitives from a cube to a box where appropriate

If you have fixed width sprites in a sheet, then use the Pixel_W and Pixel_H to set the bounding widths
This will force a gap between sprites

There's much that can be done to optimise the code, including 

    : PNG file handling
    : Colour Exception/Chroma Key Tables
    : Parameters etc.



Usage :-

  PNG2OBJ.py Filename

  i.e. ./PNG2OBJ SpriteSheet

  Do not include the File Extension - Lazy I know... 

  Two output files are created

      Filename.obj    <-- Contains the WaveFront OBJ 3D Vertices information
      Filename.txt    <-- Used for debugging, showing an ASCII representation 
                          Of what pixels were processed.

V1.00 - 3rd June 2022 - The Platty Joobs Edition ;)
                        Initial Release

