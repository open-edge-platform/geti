# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Build a versioned, optionally-signed MSIX package for the Geti desktop app.

This tool is the single entry point that turns the compiled Tauri artifacts into
an installable ``.msix``. It is intentionally dependency-free (Python standard
library only) so it runs from a bare ``python`` on any CI runner, and its
version/manifest logic is pure and unit-tested (see ``tests/test_build_msix.py``)
so it can be validated on non-Windows hosts even though ``makeappx``/``signtool``
only exist on Windows.

Pipeline (``build`` command):

1. Resolve the release version (``--version`` > ``GETI_MSIX_VERSION`` env >
   ``tauri.conf.json``) and normalise it to the MSIX 4-part
   ``Major.Minor.Build.Revision`` form.
2. Render ``AppxManifest.xml`` (template) with that version. ``Name`` and
   ``Publisher`` are preserved verbatim so Windows treats a newer package as an
   in-place upgrade rather than a side-by-side install.
3. Stage the app payload (``geti_ui.exe`` + ``geti-backend`` sidecar +
   ``_internal/`` + ``Assets/``) into a clean directory.
4. Pack it with the Windows SDK ``makeappx``.
5. Sign it with ``signtool`` when a certificate is provided.

Run ``python build_msix.py --help`` (or ``<command> --help``) for all options.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths (relative to this file: <repo>/application/ui/src-tauri/msix/)
# --------------------------------------------------------------------------- #
MSIX_DIR = Path(__file__).resolve().parent
SRC_TAURI_DIR = MSIX_DIR.parent
TAURI_CONF = SRC_TAURI_DIR / "tauri.conf.json"
MANIFEST_TEMPLATE = MSIX_DIR / "AppxManifest.xml"
ASSETS_DIR = MSIX_DIR / "Assets"
DEFAULT_TARGET_DIR = SRC_TAURI_DIR / "target" / "release"

# Payload file names produced by `tauri build`.
UI_EXE = "geti_ui.exe"  # from Cargo package `geti_ui`
SIDECAR_GLOB = "geti-backend*.exe"  # Tauri externalBin (may carry a target triple)
SIDECAR_STAGED_NAME = "geti-backend.exe"  # name the backend expects (see backend.rs)
INTERNAL_DIR = "_internal"  # PyInstaller runtime bundled as a Tauri resource

# MSIX version parts are unsigned 16-bit integers.
_MAX_VERSION_PART = 65535


# --------------------------------------------------------------------------- #
# Pure helpers (unit-tested, no filesystem/Windows dependency)
# --------------------------------------------------------------------------- #
def normalize_msix_version(version: str) -> str:
    """Normalise a semver-ish string to an MSIX ``Major.Minor.Build.Revision``.

    - Leading ``v`` and surrounding whitespace are ignored.
    - Build metadata (``+...``) and pre-release tags (``-rc1``) are dropped, since
      MSIX versions must be purely numeric. A pre-release therefore maps to the
      same numeric version as its final release, so releases must not ship a
      pre-release tag as their package version (a warning is emitted).
    - 1 to 4 numeric, dot-separated parts are accepted and right-padded with
      zeros to exactly four. Each part must be in ``0..=65535``.

    >>> normalize_msix_version("3.1.0")
    '3.1.0.0'
    >>> normalize_msix_version("v2")
    '2.0.0.0'
    """
    raw = version.strip()
    if raw.startswith("v"):
        raw = raw[1:]
    # Drop build metadata then pre-release, keeping only the numeric core.
    core = raw.split("+", 1)[0]
    if "-" in core:
        core = core.split("-", 1)[0]
        print(
            f"warning: stripped pre-release/build tag from version '{version}' -> "
            f"'{core}'; MSIX versions must be numeric",
            file=sys.stderr,
        )

    parts = core.split(".")
    if not 1 <= len(parts) <= 4:
        raise ValueError(
            f"invalid version '{version}': expected 1 to 4 dotted numeric parts"
        )

    numbers: list[int] = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"invalid version '{version}': non-numeric part '{part}'")
        value = int(part)
        if value > _MAX_VERSION_PART:
            raise ValueError(
                f"invalid version '{version}': part '{part}' exceeds {_MAX_VERSION_PART}"
            )
        numbers.append(value)

    numbers += [0] * (4 - len(numbers))
    return ".".join(str(n) for n in numbers)


# Matches the `Version="..."` attribute of the <Identity> element regardless of
# attribute order, so the template's current value is irrelevant.
_IDENTITY_VERSION_RE = re.compile(
    r'(<Identity\b[^>]*?\bVersion=")[^"]*(")',
    re.DOTALL,
)


def render_manifest(template_text: str, version: str) -> str:
    """Return ``template_text`` with the ``<Identity>`` version set to ``version``.

    ``version`` is normalised first. Exactly one ``<Identity>`` element with a
    ``Version`` attribute must be present, otherwise a ``ValueError`` is raised.
    """
    normalized = normalize_msix_version(version)
    rendered, count = _IDENTITY_VERSION_RE.subn(
        rf"\g<1>{normalized}\g<2>", template_text
    )
    if count == 0:
        raise ValueError(
            'no <Identity ... Version="..."> attribute found in manifest template'
        )
    if count > 1:
        raise ValueError(
            'multiple <Identity ... Version="..."> attributes found in manifest template'
        )
    return rendered


def read_project_version(tauri_conf: Path = TAURI_CONF) -> str:
    """Read the app version from ``tauri.conf.json`` (the source of truth)."""
    data = json.loads(tauri_conf.read_text(encoding="utf-8"))
    version = data.get("version")
    if not version:
        raise ValueError(f"no 'version' field in {tauri_conf}")
    return str(version)


def resolve_version(explicit: str | None, tauri_conf: Path = TAURI_CONF) -> str:
    """Resolve the release version: CLI flag > env > tauri.conf.json."""
    return (
        explicit
        or os.environ.get("GETI_MSIX_VERSION")
        or read_project_version(tauri_conf)
    )


# --------------------------------------------------------------------------- #
# Filesystem staging
# --------------------------------------------------------------------------- #
def _find_sidecar(target_dir: Path, override: Path | None) -> Path:
    """Locate the ``geti-backend`` sidecar, tolerating a target-triple suffix."""
    if override is not None:
        if not override.is_file():
            raise FileNotFoundError(f"sidecar not found at --sidecar path: {override}")
        return override
    matches = sorted(target_dir.glob(SIDECAR_GLOB))
    if not matches:
        raise FileNotFoundError(
            f"backend sidecar ({SIDECAR_GLOB}) not found in {target_dir}. "
            "Run `npx tauri build` first, or pass --sidecar."
        )
    return matches[0]


def stage_payload(
    staging_dir: Path,
    version: str,
    *,
    target_dir: Path = DEFAULT_TARGET_DIR,
    sidecar: Path | None = None,
    internal_dir: Path | None = None,
) -> Path:
    """Assemble the MSIX payload into ``staging_dir`` and return it.

    Every required artifact is validated up front with an actionable error so a
    misconfigured build fails fast instead of producing a broken package.
    """
    ui_exe = target_dir / UI_EXE
    if not ui_exe.is_file():
        raise FileNotFoundError(
            f"UI executable not found at {ui_exe}. Run `npx tauri build` first, "
            "or pass --target-dir."
        )
    sidecar_path = _find_sidecar(target_dir, sidecar)
    internal = internal_dir or (target_dir / INTERNAL_DIR)
    if not internal.is_dir():
        raise FileNotFoundError(
            f"'{INTERNAL_DIR}' runtime directory not found at {internal}. "
            "Run `npx tauri build` first, or pass --internal-dir."
        )
    if not ASSETS_DIR.is_dir():
        raise FileNotFoundError(f"MSIX Assets directory not found at {ASSETS_DIR}")

    # Start from a clean staging directory for reproducible packages.
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    # Rendered manifest.
    manifest_text = render_manifest(
        MANIFEST_TEMPLATE.read_text(encoding="utf-8"), version
    )
    (staging_dir / "AppxManifest.xml").write_text(manifest_text, encoding="utf-8")

    # App payload.
    shutil.copy2(ui_exe, staging_dir / UI_EXE)
    shutil.copy2(sidecar_path, staging_dir / SIDECAR_STAGED_NAME)
    shutil.copytree(internal, staging_dir / INTERNAL_DIR)
    shutil.copytree(ASSETS_DIR, staging_dir / "Assets")

    return staging_dir


# --------------------------------------------------------------------------- #
# Windows SDK tooling (makeappx / signtool)
# --------------------------------------------------------------------------- #
def _find_windows_sdk_tool(name: str, override: str | None) -> str:
    """Resolve a Windows SDK executable: override > PATH > Windows Kits search."""
    if override:
        return override
    on_path = shutil.which(name)
    if on_path:
        return on_path
    # Fall back to scanning the default Windows Kits install, newest SDK first.
    for root in (
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("ProgramFiles", r"C:\Program Files"),
    ):
        bin_dir = Path(root) / "Windows Kits" / "10" / "bin"
        if not bin_dir.is_dir():
            continue
        candidates = sorted(bin_dir.glob(f"*/x64/{name}"), reverse=True)
        if candidates:
            return str(candidates[0])
    raise FileNotFoundError(
        f"'{name}' not found on PATH or under the Windows 10 SDK. Install the "
        f"Windows SDK or pass an explicit path."
    )


def _run(cmd: list[str]) -> None:
    """Run a subprocess, echoing the command and raising on failure."""
    printable = " ".join(str(c) for c in cmd)
    print(f"$ {printable}", flush=True)
    subprocess.run(cmd, check=True)


def pack(staging_dir: Path, output: Path, *, makeappx: str | None = None) -> Path:
    """Pack ``staging_dir`` into an ``.msix`` at ``output`` using ``makeappx``."""
    tool = _find_windows_sdk_tool("makeappx.exe", makeappx)
    output.parent.mkdir(parents=True, exist_ok=True)
    _run([tool, "pack", "/d", str(staging_dir), "/p", str(output), "/o"])
    return output


def sign(
    package: Path,
    *,
    signtool: str | None = None,
    cert_file: str | None = None,
    cert_password: str | None = None,
    cert_thumbprint: str | None = None,
    timestamp_url: str | None = None,
) -> None:
    """Sign ``package`` with ``signtool``.

    Credentials come from the arguments, falling back to environment variables
    (``GETI_MSIX_CERT``, ``GETI_MSIX_CERT_PASSWORD``, ``GETI_MSIX_CERT_THUMBPRINT``,
    ``GETI_MSIX_TIMESTAMP_URL``). Provide either a PFX file or a store thumbprint;
    the certificate subject must match the manifest ``Publisher``.
    """
    cert_file = cert_file or os.environ.get("GETI_MSIX_CERT")
    cert_password = cert_password or os.environ.get("GETI_MSIX_CERT_PASSWORD")
    cert_thumbprint = cert_thumbprint or os.environ.get("GETI_MSIX_CERT_THUMBPRINT")
    timestamp_url = timestamp_url or os.environ.get("GETI_MSIX_TIMESTAMP_URL")

    if not cert_file and not cert_thumbprint:
        raise ValueError(
            "signing requested but no certificate provided: pass --cert-file/--cert-thumbprint "
            "or set GETI_MSIX_CERT / GETI_MSIX_CERT_THUMBPRINT."
        )

    tool = _find_windows_sdk_tool("signtool.exe", signtool)
    cmd: list[str] = [tool, "sign", "/fd", "SHA256"]
    if cert_file:
        cmd += ["/f", cert_file]
        if cert_password:
            cmd += ["/p", cert_password]
    if cert_thumbprint:
        cmd += ["/sha1", cert_thumbprint]
    if timestamp_url:
        cmd += ["/tr", timestamp_url, "/td", "SHA256"]
    cmd.append(str(package))
    _run(cmd)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _wants_signing(args: argparse.Namespace) -> bool:
    return bool(
        args.sign
        or args.cert_file
        or args.cert_thumbprint
        or os.environ.get("GETI_MSIX_CERT")
        or os.environ.get("GETI_MSIX_CERT_THUMBPRINT")
    )


def _cmd_version(args: argparse.Namespace) -> int:
    version = resolve_version(args.version)
    print(normalize_msix_version(version))
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    version = resolve_version(args.version)
    rendered = render_manifest(MANIFEST_TEMPLATE.read_text(encoding="utf-8"), version)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Wrote rendered manifest to {args.output}")
    else:
        sys.stdout.write(rendered)
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    version = resolve_version(args.version)
    normalized = normalize_msix_version(version)
    staging_dir = Path(args.staging_dir)
    output = (
        Path(args.output)
        if args.output
        else MSIX_DIR / "dist" / f"Geti_{normalized}.msix"
    )

    print(f"▶ Packaging Geti MSIX version {normalized}")
    stage_payload(
        staging_dir,
        version,
        target_dir=Path(args.target_dir),
        sidecar=Path(args.sidecar) if args.sidecar else None,
        internal_dir=Path(args.internal_dir) if args.internal_dir else None,
    )
    print(f"▶ Staged payload at {staging_dir}")

    pack(staging_dir, output, makeappx=args.makeappx)
    print(f"✅ Packed {output}")

    if _wants_signing(args):
        sign(
            output,
            signtool=args.signtool,
            cert_file=args.cert_file,
            cert_password=args.cert_password,
            cert_thumbprint=args.cert_thumbprint,
            timestamp_url=args.timestamp_url,
        )
        print(f"✅ Signed {output}")
    else:
        print(
            "⚠ Package is UNSIGNED. Provide --cert-file/--cert-thumbprint (or "
            "GETI_MSIX_CERT*/env) to sign; unsigned packages require a trusted "
            "test certificate to sideload."
        )

    print(f"✅ MSIX ready: {output}")
    return 0


def _add_common_version_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--version",
        help="Release version (default: GETI_MSIX_VERSION env, else tauri.conf.json).",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_version = sub.add_parser(
        "version", help="Print the normalised MSIX version and exit."
    )
    _add_common_version_arg(p_version)
    p_version.set_defaults(func=_cmd_version)

    p_render = sub.add_parser(
        "render", help="Render the AppxManifest.xml with the resolved version."
    )
    _add_common_version_arg(p_render)
    p_render.add_argument(
        "-o", "--output", help="Write to this file (default: stdout)."
    )
    p_render.set_defaults(func=_cmd_render)

    p_build = sub.add_parser(
        "build", help="Stage, pack and (optionally) sign the MSIX."
    )
    _add_common_version_arg(p_build)
    p_build.add_argument(
        "-o", "--output", help="Output .msix path (default: dist/Geti_<version>.msix)."
    )
    p_build.add_argument(
        "--staging-dir",
        default=str(MSIX_DIR / "build" / "staging"),
        help="Payload staging dir.",
    )
    p_build.add_argument(
        "--target-dir",
        default=str(DEFAULT_TARGET_DIR),
        help="Where `tauri build` put its output.",
    )
    p_build.add_argument(
        "--sidecar", help="Explicit path to the geti-backend sidecar exe."
    )
    p_build.add_argument(
        "--internal-dir", help="Explicit path to the _internal directory."
    )
    p_build.add_argument(
        "--makeappx", help="Path to makeappx.exe (default: PATH / Windows SDK)."
    )
    p_build.add_argument(
        "--sign",
        action="store_true",
        help="Force signing (fails if no cert is provided).",
    )
    p_build.add_argument(
        "--signtool", help="Path to signtool.exe (default: PATH / Windows SDK)."
    )
    p_build.add_argument(
        "--cert-file", help="PFX certificate file (env: GETI_MSIX_CERT)."
    )
    p_build.add_argument(
        "--cert-password", help="PFX password (env: GETI_MSIX_CERT_PASSWORD)."
    )
    p_build.add_argument(
        "--cert-thumbprint",
        help="Store certificate thumbprint (env: GETI_MSIX_CERT_THUMBPRINT).",
    )
    p_build.add_argument(
        "--timestamp-url", help="RFC 3161 timestamp URL (env: GETI_MSIX_TIMESTAMP_URL)."
    )
    p_build.set_defaults(func=_cmd_build)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"error: command failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
