# Building the Windows MSIX package

This document describes how the Geti Windows desktop app is packaged as a
versioned, signable **MSIX** whose identity supports clean **in-place upgrades**
(see [`upgrade.md`](./upgrade.md#windows-desktop-msix-app) for the user-facing
upgrade behavior).

## Overview

The build is driven by the `just package-msix` recipe
([`application/Justfile`](../Justfile)), which:

1. runs `npx tauri build` to compile the UI executable (`geti_ui.exe`), the
   bundled backend sidecar (`geti-backend.exe`) and the PyInstaller runtime
   (`_internal/`), then
2. runs [`ui/src-tauri/msix/build_msix.py`](../ui/src-tauri/msix/build_msix.py),
   which **injects the release version** into the MSIX manifest, **stages** the
   payload and **packs** (and optionally **signs**) the `.msix`.

```powershell
# From application/ (Windows, with the Windows 10 SDK installed)
just package-msix
```

## Version handling (why upgrades work)

Windows performs an **in-place upgrade** — replacing the app while keeping the
per-user data directory (`%LOCALAPPDATA%\com.intel.geti`) — only when the new
package has the **same `Identity/Name` and `Publisher`** and a **strictly higher
4-part `Version`**.

- `Name` (`intel.geti`) and `Publisher` are constant in
  [`AppxManifest.xml`](../ui/src-tauri/msix/AppxManifest.xml) and must never
  change, or Windows would treat a new build as a _different_ app installed
  side-by-side.
- The `Version` in the checked-in manifest is a **placeholder** (`0.0.0.0`).
  `build_msix.py` always overwrites it with the resolved release version,
  normalised to `Major.Minor.Build.Revision` (e.g. `3.1.0` → `3.1.0.0`).

The release version is resolved in this order:

1. `--version` CLI flag,
2. `GETI_MSIX_VERSION` environment variable,
3. the `version` field in [`tauri.conf.json`](../ui/src-tauri/tauri.conf.json)
   (the source of truth).

**For every release, bump the version** (in `tauri.conf.json`, or via
`GETI_MSIX_VERSION`). Pre-release/build tags (`-rc1`, `+build`) are stripped
because MSIX versions must be numeric — do not ship a pre-release string as the
package version, or two builds could collide on the same numeric version.

Inspect what would be produced without building:

```bash
# Print the normalised MSIX version
python ui/src-tauri/msix/build_msix.py version           # e.g. 3.0.0.0
python ui/src-tauri/msix/build_msix.py version --version 3.1.0

# Print the rendered manifest
python ui/src-tauri/msix/build_msix.py render
```

## Signing

Provide a certificate whose subject matches the manifest `Publisher`
(`CN=Intel Corporation, O=Intel Corporation, S=California, C=US`). Either a PFX
file or a certificate-store thumbprint works:

```powershell
$env:GETI_MSIX_CERT = "C:\path\to\intel-codesign.pfx"
$env:GETI_MSIX_CERT_PASSWORD = "<pfx password>"
$env:GETI_MSIX_TIMESTAMP_URL = "http://timestamp.digicert.com"  # optional but recommended
just package-msix
```

or with a thumbprint from the machine/user store:

```powershell
$env:GETI_MSIX_CERT_THUMBPRINT = "ABCD...EF"
just package-msix
```

Without a certificate the package is built **unsigned** (a warning is printed).
Unsigned packages can only be sideloaded after their test certificate is trusted
on the target machine.

## Requirements

- **Windows 10 SDK** — provides `makeappx.exe` and `signtool.exe`. The script
  locates them on `PATH` or under `C:\Program Files (x86)\Windows Kits\10\bin`;
  override with `--makeappx` / `--signtool` if needed.
- Node.js + the Rust toolchain (for `tauri build`).
- Python 3 (standard library only — no extra packages needed for the packager).

## Testing the packager

The version/manifest/staging logic is covered by standard-library unit tests
that run on any platform (no Windows SDK required):

```bash
cd ui/src-tauri/msix
python -m unittest discover -s tests
```

## Output

The signed/unsigned package is written to
`ui/src-tauri/msix/dist/Geti_<version>.msix` by default (override with
`--output`). The staging directory (`ui/src-tauri/msix/build/staging/`) is
recreated on each run for reproducibility.
