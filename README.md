![License: Custom MIT](https://img.shields.io/badge/license-MIT--NC-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Raspberry%20Pi-lightgrey)

# PNG2ObjV3

Convert PNG images into 3D printable `.OBJ` files or scalable `.SVG` vectors — with support for sprite slicing, optical illusions, physical layering, and more.

> Originally built as a quick hack to automate CAD work — now a full-featured CLI tool for retro pixel artists, 3D print modellers, and tinkerers.

---

## 🔧 What It Does

- ✅ Convert pixel images (e.g. retro sprites) into:
  - Flat `.OBJ` files
  - Layered or towered `.OBJ` files
  - Optical illusion `.SVG` files
  - Frame templates for physical mounting/cutting
- ✅ Generate `.MTL` files to colour match `.OBJ` outputs
- ✅ Add joints to prevent 3D print breakages
- ✅ Slice sprite sheets into individual frames
- ✅ Define colour inclusions/exclusions with precision
- ✅ Supports per-pixel scaling, grid alignment, and Z-depth stacking
- ✅ Platform-agnostic (macOS, Linux, Raspberry Pi tested)

---

## 📸 Examples

| Option                         | Description                                                           |
|-------------------------------|------------------------------------------------------------------------|
| `--flat`                      | All colours at same Z height                                          |
| `--layered`                   | One colour per OBJ layer                                              |
| `--tower`                     | Colours stacked by pixel count or custom order                        |
| `--illusion`                  | Wobbling SVG illusions using positive/negative space                  |
| `--frame400`                  | SVG layout with MAPED cutter offsets for The Range 400mm frame        |
| `--spritewidth` /<br>`--spriteheight` | Extract each frame from a sprite sheet                              |

📘 Full walkthroughs, parameter lists, and visual outputs are available in the [📄 PDF Manual](./User%20Manual%20V01c.pdf).

---

## 🚀 Getting Started

### Requirements

- Python ≥ 3.8.5

```bash
pip install pypng
```

### Basic Usage

Convert a PNG to a 3D printable OBJ:
```bash
python3 PNG2ObjV3.py mySprite.png
```

Create an illusion-style SVG:
```bash
python3 PNG2ObjV3.py -svg -illusion -svgaddpng mySprite.png
```

Exclude background colour:
```bash
python3 PNG2ObjV3.py mySprite.png -el #000000
```

Layered OBJ with joints and material file:
```bash
python3 PNG2ObjV3.py mySprite.png --layered --joints --mtl
```

---

## 🧠 Notable Features

- 🧱 **Joint Injection**: Adds printable support between loose pixels
- 🎨 **Material (.MTL) Output**: For use in slicers that support colour recognition
- 📏 **Per-pixel Scaling**: Control object dimensions in mm directly via CLI
- 🖼️ **SVG Rounding**: Adjustable corner radii for pixel-to-curve rendering
- 📦 **Batch & Parametric Processing**: Ideal for sprite sheets or QR plaque generation

---

## 🧪 Under Development

- `--parametricTest` — experiments with sine-modulated OBJ surface shaping
- Future plans: GUI frontend (Tkinter or web-based), auto SVG shape grouping

---

## 🛠️ Developer Notes

This project grew organically and... **got messy**. It's ripe for:

- Refactoring into classes/modules
- Improving CLI handling (use `argparse`)
- Adding test coverage
- Possibly adding a visual preview mode

Want to help? Fork and submit a pull request!

---

---

## 🧪 Setting Up a Virtual Environment

Use a Python virtual environment to isolate dependencies and keep your system clean.

### 🔧 Create the Environment

```bash
python3 -m venv venv
```

### ▶️ Activate the Environment

- **macOS / Linux:**

```bash
source venv/bin/activate
```

- **Windows (CMD):**

```cmd
venv\Scripts\activate.bat
```

- **Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

### 📦 Install Required Packages

```bash
pip install -r requirements.txt
```

### 🛑 Deactivate When Done

```bash
deactivate
```


## 📄 Manual & Documentation

📘 [**User Manual (PDF)**](./User%20Manual%20V01c.pdf) — includes command examples, visuals, and parameter explanations.

🧰 Supports:
- Affinity Designer
- Adobe Illustrator
- Inkscape / GIMP
- Any slicer software that accepts `.OBJ` and `.MTL`

---

## 👨‍💻 Author

Created by [Jason Brooks](https://www.muckypaws.com)  
Twitter/X: [@MuckyPaws](https://twitter.com/muckypaws)  
GitHub: [github.com/muckypaws](https://github.com/muckypaws)

---

## ⚖️ License

MIT License (To be confirmed in repo)

---

## 💬 Feedback or Contributions?

Raise an issue, submit a pull request, or shout into the retro computing void.  
It's crude... but it works!
