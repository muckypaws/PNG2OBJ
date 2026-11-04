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
        """Initialise an empty registry with optional colour filters.

        Args:
            exclusion (list[str] | None): hex colour codes (``"#rrggbb"``) to
                skip entirely. ``None`` is treated as an empty list.
            process_only (list[str] | None): if non-empty, the only hex colour
                codes that may be registered; every other colour is rejected.
                ``None`` is treated as an empty list (no allowlist).
        """
        self.colours = {}
        self.materials = []
        self.index = 0
        self.exclusion = exclusion if exclusion is not None else []
        self.process_only = process_only if process_only is not None else []

    def material_string(self, r, g, b):
        """Render an MTL material block for an RGB colour and store it.

        Builds a Wavefront ``newmtl``/``Kd`` block for the colour, naming the
        material after the current ``index`` and normalising each channel to the
        0.0-1.0 range, then appends it to ``materials``.

        Args:
            r (int): red channel, 0-255.
            g (int): green channel, 0-255.
            b (int): blue channel, 0-255.

        Returns:
            str: the rendered material block (also appended to ``materials``).

        Note:
            This does not advance ``index`` itself; the caller does, matching
            the original two-step ``MaterialColourAsString`` behaviour.
        """
        mult = 1.0 / 255.0

        Material = (
            f"\nnewmtl {self.index}\n"
            f"Kd {mult * r:.6f} {mult * g:.6f} {mult * b:.6f} "
            + default_mtl_params + "\n"
        )

        self.materials.append(Material)
        return Material

    def register(self, r, g, b, pixel=-1):
        """Register an RGB colour if the filter lists allow it.

        Applies the ``exclusion`` and ``process_only`` filters, records the
        colour in ``colours`` the first time it is seen, and — when called for
        a real pixel (``pixel >= 0``) — emits its material block and advances
        ``index``.

        Args:
            r (int): red channel, 0-255.
            g (int): green channel, 0-255.
            b (int): blue channel, 0-255.
            pixel (int): the source pixel offset, or ``-1`` when merely probing
                whether the colour is allowed. A material block is only created
                for ``pixel >= 0``.

        Returns:
            tuple[bool, str]: ``(valid, hex_code)`` where ``hex_code`` is the
            ``"#rrggbb"`` form of the colour and ``valid`` is ``False`` when the
            colour is excluded or missing from a non-empty process-only
            allowlist, ``True`` otherwise.
        """
        # Check to see if we already have this material.
        ColourCode = f"#{r:02x}{g:02x}{b:02x}"

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
