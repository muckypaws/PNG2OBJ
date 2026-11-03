"""Material (.MTL) colour registry.

Collects the colours discovered while scanning a PNG, assigns each a Wavefront
material index, and renders the MTL `newmtl`/`Kd` blocks. This replaces the
former scattered module globals (mtl_colour_dict, mtl_final_list,
mtl_current_index) and the two colour-filter lists (exclusion / process-only)
with a single reusable object. Behaviour is preserved exactly from the original
MaterialColourAsString / addMaterialToFile functions.
"""
from png2obj.geometry import default_mtl_params


class MaterialRegistry:
    """Tracks discovered colours and the MTL material blocks emitted for them.

    Attributes:
        colours (dict[str, int]): hex colour code -> pixel count.
        materials (list[str]): rendered MTL material blocks, in creation order.
        index (int): next material index / name label.
        exclusion (list[str]): hex colours to skip entirely.
        process_only (list[str]): if non-empty, the only hex colours allowed.
    """

    def __init__(self, exclusion=None, process_only=None):
        self.colours = {}
        self.materials = []
        self.index = 0
        self.exclusion = exclusion if exclusion is not None else []
        self.process_only = process_only if process_only is not None else []

    def material_string(self, r, g, b):
        """Render an MTL block for an RGB colour (0-255) and store it.

        Returns the material string. Does not advance ``index`` itself (the
        caller does, matching the original two-step behaviour).
        """
        myFormatter = "{0:.6f}"

        mult = 1.0 / 255.0

        Material = f"\nnewmtl {self.index}\n" + \
            f"Kd " + str(myFormatter.format(mult * r)) + " " + \
            str(myFormatter.format(mult * g)) + " " + \
            str(myFormatter.format(mult * b)) + " " + \
            default_mtl_params + "\n"

        self.materials.append(Material)
        return Material

    def register(self, r, g, b, pixel=-1):
        """Register an RGB colour if allowed by the filter lists.

        Returns (valid, hex_code). ``valid`` is False when the colour is
        excluded or not in the process-only allowlist. A material block is
        created (and ``index`` advanced) the first time a colour is seen with
        a real pixel (pixel >= 0).
        """
        # Check to see if we already have this material.
        ColourCode = "#" + '{:02x}'.format(r) + '{:02x}'.format(g) + '{:02x}'.format(b)

        # Is Pixel in excluded list?
        if ColourCode in self.exclusion:
            return False, ColourCode

        if len(self.process_only) > 0:
            if ColourCode not in self.process_only:
                return False, ColourCode

        if not ColourCode in self.colours and not ColourCode in self.exclusion:
            self.colours[ColourCode] = 0

            if pixel >= 0:
                self.material_string(r, g, b)
                self.index += 1
                return True, ColourCode

        return True, ColourCode
