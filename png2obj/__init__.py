"""png2obj: modular internals for the PNG2ObjV3 pixel-to-3D/SVG converter.

This package was extracted, in behaviour-preserving steps, from the original
single-file ``PNG2ObjV3.py``. Each module owns one concern:

    runtime         shared per-run state objects (IMAGE / MATERIALS / SVG) and
                    the global flags (DEBUG, defaults) the other modules read.
    geometry        immutable cube / joint vertex, normal and face tables, the
                    default material parameters and the ``update_vert`` helper.
    materials       the ``MaterialRegistry`` that collects discovered colours
                    and renders Wavefront ``.mtl`` material blocks.
    imageprocessing PNG loading and per-pixel colour/ index extraction.
    objectcreation  the pixel-scanning core that emits Wavefront ``.obj`` 3D
                    geometry (flat, layered, tower and parametric modes).
    svg_primitives  pure, low-level SVG element string builders and the raster
                    helpers (arrays, Bresenham circles) used by illusions.
    svg             high-level SVG generation: pixel grids, 400mm frame guides
                    and the diagonal / circular optical-illusion renderers.

The command-line entry point remains ``PNG2ObjV3.py``, which wires these
modules together behind an argparse interface.

Attributes:
    __version__ (str): the package / tool version, mirroring the CLI banner.
"""

__version__ = "3.0.0"
