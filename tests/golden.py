#!/usr/bin/env python3
"""Golden-output regression harness for PNG2ObjV3.

Runs the converter across a matrix of modes x test images and records a
normalised fingerprint (sha256) of every output file plus stdout. The point is
to guarantee that refactoring does not change behaviour: capture a baseline
from the known-good code, then `check` after each change.

Normalisation strips the only sources of run-to-run variation:
  * timestamps written into OBJ/MTL headers and log lines (datetime.now())
  * absolute paths of the per-case output directory

Optical-illusion output uses random.randint; tests/_runner.py seeds the RNG
with a fixed value so that output is reproducible too.

Usage:
    python tests/golden.py capture            # write baseline (run on good code)
    python tests/golden.py check              # compare current code to baseline
    python tests/golden.py list               # print the case matrix

Environment:
    GOLDEN_DIR   where baselines/artifacts live (default: tests/_golden)
    GOLDEN_SEED  RNG seed for reproducible illusions (default: 1234)
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "PNG2ObjV3.py"
RUNNER = REPO / "tests" / "_runner.py"
GOLDEN_DIR = Path(os.environ.get("GOLDEN_DIR", REPO / "tests" / "_golden"))
SEED = os.environ.get("GOLDEN_SEED", "1234")

# Generated fixtures for the indexed/greyscale feature (scope E). These are
# written deterministically by _ensure_fixtures() because *.png is gitignored;
# the pixel data is fixed so the derived output is reproducible run to run.
FIXTURE_DIR = REPO / "tests" / "fixtures"

# Test images shipped in the repo (see testimages.zip / README).
IMAGES = {
    "stride": REPO / "JSWStride.png",
    "single": REPO / "JSWStrideSingle.png",
    "stand": REPO / "JSWStand.png",
    "phil": REPO / "Phil.png",
    "willy": REPO / "PlatformWilly.png",
    "sheet": REPO / "SpriteSheet.png",
    # scope E fixtures (generated on demand, not shipped).
    "grey": FIXTURE_DIR / "grey8.png",
    "palette": FIXTURE_DIR / "palette_alpha.png",
}


def _ensure_fixtures():
    """Write the greyscale and palette (with transparency) fixtures.

    Used by the indexed/greyscale support cases (scope E). The bytes are fully
    deterministic so the converter output is reproducible. Regenerated every
    run because the files are gitignored (``*.png``) and never committed.
    """
    import png  # pypng; already required by the converter.

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    # --- 8-bit greyscale, 8x6: a mix of grey levels incl. pure black/white. ---
    grey_rows = [
        [0, 32, 64, 96, 128, 160, 192, 255],
        [255, 192, 160, 128, 96, 64, 32, 0],
        [0, 0, 128, 128, 255, 255, 0, 0],
        [64, 64, 64, 64, 64, 64, 64, 64],
        [0, 255, 0, 255, 0, 255, 0, 255],
        [200, 200, 10, 10, 200, 200, 10, 10],
    ]
    with open(IMAGES["grey"], "wb") as fp:
        png.Writer(width=8, height=6, greyscale=True, bitdepth=8).write(fp, grey_rows)

    # --- 8-bit palette/indexed, 8x6, index 0 fully transparent (alpha 0). ---
    palette = [
        (0, 0, 0, 0),        # 0: transparent background
        (237, 28, 36, 255),  # 1: red
        (34, 177, 76, 255),  # 2: green
        (63, 72, 204, 255),  # 3: blue
    ]
    pal_rows = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 2, 2, 3, 3, 0],
        [0, 1, 2, 3, 1, 2, 3, 0],
        [0, 2, 2, 1, 1, 3, 3, 0],
        [0, 3, 1, 2, 3, 1, 2, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    with open(IMAGES["palette"], "wb") as fp:
        png.Writer(width=8, height=6, palette=palette, bitdepth=8).write(fp, pal_rows)

# (case_name, image_key, extra_args). Every case passes -outfile so output
# lands in the per-case dir and nothing leaks into the repo root.
CASES = [
    # --- OBJ modes ---
    ("obj_basic_stride", "stride", []),
    ("obj_basic_single", "single", []),
    ("obj_basic_phil", "phil", []),
    ("obj_mtl", "single", ["--mtl"]),
    ("obj_mtl_noframe", "single", ["--mtl", "-nf"]),
    ("obj_exclude", "willy", ["--mtl", "-nf", "-el", "#000000", "#00ff00"]),
    ("obj_sort_layered", "willy", ["--mtl", "-nf", "-s", "--layered"]),
    ("obj_reversesort", "willy", ["--mtl", "-nf", "-rs"]),
    ("obj_processcolours_layered", "willy",
     ["--mtl", "-nf", "-pc", "#bdbdbd", "#bf00bf", "--layered"]),
    ("obj_bgh_exclude", "willy", ["--mtl", "-s", "-bgh", "2.0", "-el", "#000000"]),
    ("obj_bgh_layered_lm", "single",
     ["--mtl", "-bgh", "2.0", "-lm", "5.0", "--layered"]),
    ("obj_tower", "willy", ["--mtl", "-nf", "--tower"]),
    ("obj_joints", "willy", ["--mtl", "-nf", "-j"]),
    ("obj_maxdims", "single", ["-mw", "100", "-mh", "100", "-md", "10"]),
    ("obj_nextlayeronly", "willy", ["--mtl", "-nf", "--layered", "-nl"]),
    ("obj_startz", "single", ["--mtl", "-sz", "5.0"]),
    ("obj_listcolours", "willy", ["-lc"]),
    ("obj_sheet_sprites", "sheet", ["--mtl", "-nf", "-sw", "16", "-sh", "16"]),

    # --- SVG modes (RNG-seeded for illusions) ---
    ("svg_basic", "stride", ["-svg"]),
    ("svg_circle", "stride", ["-svg", "-svgrpx", "100", "-svgrpy", "100"]),
    ("svg_square", "stride", ["-svg", "-svgrpx", "0", "-svgrpy", "0"]),
    ("svg_exclude", "stride", ["-svg", "-el", "#000000", "-svgrpx", "0", "-svgrpy", "0"]),
    ("svg_pixelsize", "stride", ["-svg", "-svgpw", "10", "-svgph", "15"]),
    ("svg_outline", "stride", ["-svg", "-el", "#000000", "-outline"]),
    ("svg_f400_ugc", "stride", ["-svg", "-el", "#000000", "-f400", "-ugc"]),
    ("svg_f400_outline_png", "stride",
     ["-svg", "-el", "#000000", "-f400", "-outline", "-svgaddpng"]),
    ("svg_illusion", "stride", ["-svg", "-el", "#000000", "-illusion"]),
    ("svg_illusion_png", "stride", ["-svg", "-el", "#000000", "-illusion", "-svgaddpng"]),
    ("svg_illusion_png_ugc", "stride",
     ["-svg", "-el", "#000000", "-illusion", "-svgaddpng", "-ugc"]),
    ("svg_illusion_newtable", "stride",
     ["-svg", "-el", "#000000", "-illusion", "-ict", "#D93C41", "#781314",
      "#3F53FF", "#020078", "-ugc"]),
    ("svg_illusion_circle", "stride", ["-svg", "-el", "#000000", "-illusion", "-ilc"]),
    ("svg_illusion_streak", "stride", ["-svg", "-el", "#000000", "-illusion", "-stmax", "8"]),
    ("svg_illusion_cset", "stride", ["-svg", "-el", "#000000", "-illusion", "-cset", "2"]),

    # --- scope E: greyscale + palette/indexed PNG support ---
    ("grey_obj", "grey", ["--mtl"]),
    ("grey_svg", "grey", ["-svg"]),
    ("palette_obj", "palette", ["--mtl"]),
    ("palette_svg", "palette", ["-svg"]),
]

# ISO timestamp like 2026-11-03 12:44:36.863969
_TS = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+")


def normalise(text: str, case_dir: Path) -> str:
    """Remove run-to-run variation (timestamps, the case output path)."""
    text = _TS.sub("<TS>", text)
    text = text.replace(str(case_dir), "<OUT>")
    text = text.replace(str(case_dir.resolve()), "<OUT>")
    # The repo path appears in echoed filenames; neutralise it too.
    text = text.replace(str(REPO.resolve()), "<REPO>")
    return text


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def run_case(name, image_key, extra, work_root):
    case_dir = work_root / name
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    image = IMAGES[image_key]
    outfile = case_dir / "out"
    argv = [str(image), "-outfile", str(outfile)] + extra

    proc = subprocess.run(
        [sys.executable, str(RUNNER), SEED, str(SCRIPT), "--", *argv],
        cwd=case_dir, capture_output=True, text=True,
    )

    # Fingerprint every output file (sorted for stability).
    files = {}
    for path in sorted(case_dir.rglob("*")):
        if path.is_file():
            raw = path.read_text("utf-8", "replace")
            rel = path.relative_to(case_dir).as_posix()
            files[rel] = sha(normalise(raw, case_dir))

    stdout_norm = normalise(proc.stdout, case_dir)
    return {
        "returncode": proc.returncode,
        "stdout": sha(stdout_norm),
        "files": files,
    }, stdout_norm


def run_all():
    _ensure_fixtures()
    work_root = GOLDEN_DIR / "work"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)
    result = {}
    stdouts = {}
    for name, image_key, extra in CASES:
        if not IMAGES[image_key].exists():
            print(f"  SKIP {name}: missing image {IMAGES[image_key].name}")
            continue
        fp, stdout_norm = run_case(name, image_key, extra, work_root)
        result[name] = fp
        stdouts[name] = stdout_norm
        nfiles = len(fp["files"])
        print(f"  ran  {name:32s} rc={fp['returncode']} files={nfiles}")
    return result, stdouts


def cmd_capture():
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    print("Capturing baseline...")
    result, _ = run_all()
    (GOLDEN_DIR / "baseline.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(f"\nBaseline written: {GOLDEN_DIR / 'baseline.json'} ({len(result)} cases)")


def cmd_check():
    baseline_path = GOLDEN_DIR / "baseline.json"
    if not baseline_path.exists():
        print("No baseline. Run: python tests/golden.py capture")
        return 2
    baseline = json.loads(baseline_path.read_text())
    print("Checking against baseline...")
    current, _ = run_all()

    problems = []
    for name in baseline:
        if name not in current:
            problems.append(f"{name}: MISSING from current run")
            continue
        b, c = baseline[name], current[name]
        if b["returncode"] != c["returncode"]:
            problems.append(f"{name}: exit {b['returncode']} -> {c['returncode']}")
        if b["stdout"] != c["stdout"]:
            problems.append(f"{name}: stdout differs")
        b_files, c_files = b["files"], c["files"]
        for f in sorted(set(b_files) | set(c_files)):
            if f not in c_files:
                problems.append(f"{name}: output file removed: {f}")
            elif f not in b_files:
                problems.append(f"{name}: new output file: {f}")
            elif b_files[f] != c_files[f]:
                problems.append(f"{name}: output changed: {f}")
    for name in current:
        if name not in baseline:
            problems.append(f"{name}: NEW case not in baseline")

    print()
    if problems:
        print(f"FAIL: {len(problems)} difference(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"PASS: all {len(baseline)} cases match baseline.")
    return 0


def cmd_list():
    for name, image_key, extra in CASES:
        print(f"{name:32s} {IMAGES[image_key].name:22s} {' '.join(extra)}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "capture":
        cmd_capture(); return 0
    if cmd == "check":
        return cmd_check()
    if cmd == "list":
        cmd_list(); return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
