# PNG2OBJ — Packaging & Standalone Builds

This directory contains everything needed to compile the **PNG2OBJ command-line
tool** into standalone, native applications and installers for Linux, macOS and
Windows, using [Nuitka](https://nuitka.net/).

The entry point for every build is **`PNG2ObjV3.py`** (the argparse CLI that
imports the `png2obj` package and `png`/pypng). Nuitka runs it as `__main__`,
so the CLI behaves exactly as when launched with the interpreter.

> **Scope:** these builds target the current **CLI**. A PySide6 + VTK GUI is
> planned for later; every build/packaging file has clearly marked
> `GUI EXTENSION POINT` comments showing where to enable it. See
> [Extending for the future GUI](#extending-for-the-future-gui).

---

## Layout

```
packaging/
├── nuitka_common.txt        # SINGLE source of truth for shared Nuitka flags
├── build_linux.sh           # Linux  : --standalone --onefile  -> dist/png2obj
├── build_macos.sh           # macOS  : --macos-create-app-bundle -> PNG2OBJ.app
├── build_windows.ps1        # Windows: --standalone (+--onefile) -> png2obj.exe
├── assets/
│   ├── png2obj.png          # source icon (256×256)
│   ├── png2obj.ico          # Windows icon (derived)
│   └── png2obj.icns         # macOS icon (derived)
├── linux/
│   ├── make_appimage.sh     # standalone binary -> dist/PNG2OBJ-<arch>.AppImage
│   ├── install.sh           # per-user / system install of binary + .desktop
│   └── PNG2OBJ.desktop      # desktop entry
├── macos/
│   ├── make_dmg.sh          # PNG2OBJ.app -> dist/PNG2OBJ-<ver>.dmg
│   └── install.sh           # copy .app to /Applications, link CLI onto PATH
├── windows/
│   └── PNG2OBJ.wxs          # WiX v4 MSI authoring
└── README.md                # this file

requirements-build.txt       # build-only deps (nuitka, …)  [repo root]
.github/workflows/build.yml  # cross-OS CI build matrix       [repo root]
```

Generated artifacts land in **`dist/`** (final deliverables) with intermediate
Nuitka output in **`build/<os>/`**; both are git-ignored.

### Shared flags live in one place

All Nuitka flags common to every OS are in **`packaging/nuitka_common.txt`**
(one flag per line, `#` comments ignored). Each build script reads that file
and appends only its OS-specific flags. Change a shared flag — or enable the
future GUI — in that one file and all three builds pick it up.

---

## Prerequisites

All platforms need **Python 3.11+** and the Python deps:

```bash
python -m pip install -r requirements.txt -r requirements-build.txt
```

Plus a C toolchain per OS:

| OS      | C compiler / tools                                              | Installer tooling                       |
|---------|----------------------------------------------------------------|-----------------------------------------|
| Linux   | `gcc` or `clang`, `patchelf`; `libfuse2` to *run* AppImages     | `appimagetool` (auto-downloaded)        |
| macOS   | Xcode Command Line Tools (`xcode-select --install`)            | `create-dmg` (optional) or `hdiutil`    |
| Windows | MSVC Build Tools, or let Nuitka fetch MinGW-w64                 | WiX Toolset v4 (`dotnet tool install wix -g`) |

---

## Building locally

### Linux — standalone binary + AppImage

```bash
packaging/build_linux.sh          # -> dist/png2obj (single ELF executable)
packaging/linux/make_appimage.sh  # -> dist/PNG2OBJ-x86_64.AppImage
```

Install it for your user (adds a `.desktop` entry, icon and a `png2obj` on
`PATH`):

```bash
packaging/linux/install.sh                 # into ~/.local
sudo packaging/linux/install.sh --system   # into /usr/local
packaging/linux/install.sh --uninstall     # remove a per-user install
```

> **FUSE:** `appimagetool` and the produced AppImage normally need FUSE. In
> containers/CI without it, `make_appimage.sh` automatically falls back to
> `APPIMAGE_EXTRACT_AND_RUN=1`, and the AppImage itself can be run the same way
> (`./PNG2OBJ-x86_64.AppImage --appimage-extract-and-run …`).

### macOS — .app bundle + .dmg

```bash
packaging/build_macos.sh          # -> dist/PNG2OBJ.app
packaging/macos/make_dmg.sh       # -> dist/PNG2OBJ-3.0.0.dmg
packaging/macos/install.sh        # copy .app to /Applications (+ CLI symlink)
```

By default a host-architecture binary is built. For a universal2 binary set
`MACOS_ARCH=universal` **and** use a universal2 CPython (e.g. the python.org
installer):

```bash
MACOS_ARCH=universal packaging/build_macos.sh
```

### Windows — .exe + MSI

```powershell
packaging\build_windows.ps1         # -> dist\png2obj.exe (+ standalone .dist tree)
packaging\build_windows.ps1 -Msi    # also build dist\PNG2OBJ-3.0.0-x64.msi
```

The MSI (WiX v4) installs into `%ProgramFiles%\PNG2OBJ`, adds a Start-Menu
shortcut, offers an optional "Add to PATH" feature, and supports clean
major-upgrade and uninstall. To build the MSI by hand:

```powershell
wix build packaging\windows\PNG2OBJ.wxs `
    -arch x64 `
    -b PublishDir=build\windows\PNG2ObjV3.dist `
    -b AssetsDir=packaging\assets `
    -o dist\PNG2OBJ-3.0.0-x64.msi
```

> **WiX version:** the authoring targets **WiX v4** (and builds unchanged on
> v5). WiX v3 has no `<Files>` auto-harvest element — if you must use v3,
> harvest the `.dist` folder with `heat.exe` and reference the generated
> `ComponentGroup` instead.

---

## Building in CI

`.github/workflows/build.yml` runs a matrix across `ubuntu-latest`,
`macos-latest` and `windows-latest`. Each job checks out the repo, sets up
Python 3.11, installs the deps, runs that OS's build + packaging scripts, and
uploads the binary/app/installer as a workflow artifact
(`png2obj-<OS>`).

Nuitka **cannot cross-compile**, so this matrix is the real mechanism for
producing the macOS `.dmg` and Windows `.msi` — they cannot be built on a Linux
box.

Triggers:

- **`workflow_dispatch`** — run on demand from the *Actions* tab.
- **push of a `v*` tag** — build release artifacts for a version.

---

## What has been tested

| Target                         | Status                                                        |
|--------------------------------|---------------------------------------------------------------|
| **Linux** binary + AppImage    | ✅ **Built and smoke-tested end-to-end** on a Linux runner (see below) |
| **macOS** .app + .dmg          | ✍️ Authored for native/CI builds; verified by `shellcheck` + `bash -n` only (Nuitka cannot cross-compile from Linux) |
| **Windows** .exe + MSI         | ✍️ Authored for native/CI builds; verified by PowerShell parse + WiX XML well-formedness only |

### Linux verification (actually run)

Environment: Python 3.13, Nuitka 2.8.10, gcc 13.3.

```text
$ packaging/build_linux.sh
    -> dist/png2obj  (11 MB, stripped ELF x86-64, onefile)

$ packaging/linux/make_appimage.sh
    -> dist/PNG2OBJ-x86_64.AppImage  (12 MB)

# OBJ + material output
$ ./png2obj JSWStride -m
    exit 0 | JSWStride.obj (36 lines) + JSWStride.mtl (467 bytes)

# SVG output
$ ./png2obj JSWStride -svg
    exit 0 | JSWStride.svg (18742 bytes, valid <?xml …?>)

# AppImage (FUSE-less sandbox)
$ ./PNG2OBJ-x86_64.AppImage --appimage-extract-and-run JSWStride -m
    exit 0 | JSWStride.obj (36 lines)
```

Output from the compiled binary is byte-for-byte identical in size to the
interpreter run of the same input.

> **Note — `-m` and Nuitka onefile:** PNG2OBJ's CLI uses `-m` (write a material
> file). Nuitka onefile's "self-execution" guard otherwise intercepts a leading
> `-m`; `nuitka_common.txt` disables just that guard
> (`--no-deployment-flag=self-execution`) so the app's own flags pass through.

---

## Signing & notarization (TODO — requires your certificates)

These steps need the maintainer's own credentials and are **not** performed by
the scripts or CI. They are documented here so they can be wired in later.

### macOS — Developer ID + notarization

Unsigned `.app`/`.dmg` files are quarantined by Gatekeeper. To distribute:

1. Enroll in the Apple Developer Program; obtain a **Developer ID Application**
   certificate.
2. Codesign with hardened runtime:
   ```bash
   codesign --deep --force --options runtime \
     --sign "Developer ID Application: <NAME> (<TEAMID>)" dist/PNG2OBJ.app
   ```
3. Build the `.dmg` (`packaging/macos/make_dmg.sh`), sign it, then **notarize**:
   ```bash
   xcrun notarytool submit dist/PNG2OBJ-3.0.0.dmg \
     --apple-id <APPLE_ID> --team-id <TEAMID> --password <APP_SPECIFIC_PW> --wait
   xcrun stapler staple dist/PNG2OBJ-3.0.0.dmg
   ```

### Windows — Authenticode

Unsigned executables trip SmartScreen. To sign:

1. Obtain a code-signing certificate (OV or EV; EV avoids SmartScreen warming).
2. Sign the `.exe` **and** the `.msi`:
   ```powershell
   signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
     /f cert.pfx /p <PW> dist\png2obj.exe dist\PNG2OBJ-3.0.0-x64.msi
   ```

In CI, store certificates/passwords as encrypted **GitHub Actions secrets** and
add the signing step after the build step — never commit certificates.

---

## A note on "obfuscation" vs. security

Compiling with Nuitka translates the Python into C and bundles it as a native
binary, so the source is **not** shipped as readable `.py`/`.pyc` files. This
**raises the bar** for casual inspection and copy-paste reuse.

It is **not** true obfuscation or a security boundary. A determined party with
standard reverse-engineering tools can still analyse the binary, recover logic,
and extract bundled data/constants. Do **not** rely on Nuitka compilation to
hide secrets, license checks, or anything whose disclosure would be harmful —
anything embedded in the binary should be considered recoverable.

---

## Extending for the future GUI

When the PySide6 + VTK GUI lands, the only build change needed is in
**`packaging/nuitka_common.txt`** — uncomment the PySide6/VTK block there
(`--enable-plugin=pyside6`, Qt plugins, `--include-package=vtkmodules` + its
data). All three build scripts read that file, so no per-OS edits to the Nuitka
invocation are required. Each OS script and the installer files additionally
carry `GUI EXTENSION POINT` comments for the OS-specific niceties (drop the
Windows console, give the macOS app a Dock icon, flip the `.desktop`
`Terminal=` flag, add a GUI Start-Menu shortcut).
