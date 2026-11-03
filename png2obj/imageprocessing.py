"""Loaded-image state.

Holds the decoded PNG and the derived bounding box of visible pixels, replacing
the former loose module globals (pattern, pattern_w/h, pattern_meta, channels,
Image_Min/Max X/Y, Image_Real_Width/Height). A single instance is created and
populated at load time; defaults match the original pre-load global values (0).
"""


class LoadedImage:
    """Decoded PNG pixel grid plus the visible-pixel bounding box.

    Attributes:
        pattern: row-major pixel data as returned by pypng (list of rows).
        width (int): PNG width in pixels (was pattern_w).
        height (int): PNG height in pixels (was pattern_h).
        meta (dict): pypng metadata (was pattern_meta).
        channels (int): channels per pixel, 3 (RGB) or 4 (RGBA).
        min_x, max_x, min_y, max_y (int): bounding box of non-transparent pixels.
        real_width, real_height (int): size of that bounding box.
    """

    def __init__(self):
        self.pattern = 0
        self.width = 0
        self.height = 0
        self.meta = 0
        self.channels = 0
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0
        self.real_width = 0
        self.real_height = 0
