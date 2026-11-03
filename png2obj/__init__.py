"""png2obj: modular internals for the PNG2ObjV3 converter.

This package is being extracted, in behaviour-preserving steps, from the
original single-file PNG2ObjV3.py. Each module holds one concern:

    geometry        primitive vertex/face/normal tables and vertex helpers
    svg_primitives  low-level SVG element string builders and raster helpers

The command-line entry point remains PNG2ObjV3.py.
"""

__version__ = "3.0.0"
