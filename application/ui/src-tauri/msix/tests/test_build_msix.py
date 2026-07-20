# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the MSIX packaging tool's pure logic and staging.

These use only the standard library (``unittest``) so they run on any host
without the Windows SDK (``makeappx``/``signtool`` are not exercised here).

Run with:  python -m unittest discover -s tests   (from the msix directory)
       or:  python -m pytest                       (pytest also collects them)
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Make the sibling `build_msix.py` importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_msix as m  # noqa: E402


class NormalizeVersionTests(unittest.TestCase):
    def test_pads_to_four_parts(self) -> None:
        self.assertEqual(m.normalize_msix_version("3"), "3.0.0.0")
        self.assertEqual(m.normalize_msix_version("3.1"), "3.1.0.0")
        self.assertEqual(m.normalize_msix_version("3.1.0"), "3.1.0.0")
        self.assertEqual(m.normalize_msix_version("3.1.0.7"), "3.1.0.7")

    def test_strips_v_prefix_and_whitespace(self) -> None:
        self.assertEqual(m.normalize_msix_version("  v2.5  "), "2.5.0.0")

    def test_strips_prerelease_and_build_metadata(self) -> None:
        self.assertEqual(m.normalize_msix_version("3.1.0-rc1"), "3.1.0.0")
        self.assertEqual(m.normalize_msix_version("3.1.0+build.9"), "3.1.0.0")
        self.assertEqual(m.normalize_msix_version("3.1.0-rc1+build.9"), "3.1.0.0")

    def test_monotonic_upgrade_ordering(self) -> None:
        # A newer release must sort strictly above the previous one so Windows
        # recognises it as an in-place upgrade.
        def as_tuple(v: str) -> tuple[int, ...]:
            return tuple(int(p) for p in m.normalize_msix_version(v).split("."))

        self.assertLess(as_tuple("3.0.0"), as_tuple("3.1.0"))
        self.assertLess(as_tuple("3.1.0"), as_tuple("3.1.1"))

    def test_rejects_non_numeric(self) -> None:
        with self.assertRaises(ValueError):
            m.normalize_msix_version("3.x.0")

    def test_rejects_too_many_parts(self) -> None:
        with self.assertRaises(ValueError):
            m.normalize_msix_version("1.2.3.4.5")

    def test_rejects_out_of_range_part(self) -> None:
        with self.assertRaises(ValueError):
            m.normalize_msix_version("1.70000.0")


class RenderManifestTests(unittest.TestCase):
    TEMPLATE = (
        "<Package>\n"
        '  <Identity Name="intel.geti" '
        'Publisher="CN=Intel Corporation, O=Intel Corporation, S=California, C=US" '
        'Version="0.0.0.0"/>\n'
        "</Package>\n"
    )

    def test_injects_normalized_version(self) -> None:
        out = m.render_manifest(self.TEMPLATE, "3.1.0")
        self.assertIn('Version="3.1.0.0"', out)
        self.assertNotIn('Version="0.0.0.0"', out)

    def test_preserves_name_and_publisher(self) -> None:
        out = m.render_manifest(self.TEMPLATE, "3.1.0")
        self.assertIn('Name="intel.geti"', out)
        self.assertIn(
            "CN=Intel Corporation, O=Intel Corporation, S=California, C=US", out
        )

    def test_version_attribute_before_name(self) -> None:
        # Robust to attribute ordering.
        template = '<Package><Identity Version="0.0.0.0" Name="intel.geti"/></Package>'
        out = m.render_manifest(template, "4.2.1")
        self.assertIn('Version="4.2.1.0"', out)

    def test_raises_without_identity(self) -> None:
        with self.assertRaises(ValueError):
            m.render_manifest("<Package></Package>", "3.1.0")

    def test_real_template_renders(self) -> None:
        # The checked-in template must be renderable and change its version.
        text = m.MANIFEST_TEMPLATE.read_text(encoding="utf-8")
        out = m.render_manifest(text, "9.9.9")
        self.assertIn('Version="9.9.9.0"', out)


class ResolveVersionTests(unittest.TestCase):
    def _write_conf(self, version: str) -> Path:
        import tempfile

        tmp = Path(tempfile.mkdtemp()) / "tauri.conf.json"
        tmp.write_text(json.dumps({"version": version}), encoding="utf-8")
        return tmp

    def test_explicit_wins(self) -> None:
        conf = self._write_conf("3.0.0")
        self.assertEqual(m.resolve_version("5.5.5", conf), "5.5.5")

    def test_env_over_conf(self) -> None:
        conf = self._write_conf("3.0.0")
        import os

        os.environ["GETI_MSIX_VERSION"] = "4.4.4"
        try:
            self.assertEqual(m.resolve_version(None, conf), "4.4.4")
        finally:
            del os.environ["GETI_MSIX_VERSION"]

    def test_falls_back_to_conf(self) -> None:
        conf = self._write_conf("3.2.1")
        self.assertEqual(m.resolve_version(None, conf), "3.2.1")


class StagePayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())
        self.target = self.tmp / "target"
        self.target.mkdir()
        # Fabricate the artifacts `tauri build` would produce.
        (self.target / m.UI_EXE).write_bytes(b"MZ")
        (self.target / "geti-backend-x86_64-pc-windows-msvc.exe").write_bytes(b"MZ")
        internal = self.target / m.INTERNAL_DIR
        internal.mkdir()
        (internal / "python3.dll").write_bytes(b"x")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_stages_all_artifacts_with_rendered_manifest(self) -> None:
        staging = self.tmp / "staging"
        m.stage_payload(staging, "3.4.5", target_dir=self.target)

        self.assertTrue((staging / m.UI_EXE).is_file())
        # Sidecar is renamed to the name the backend loader expects.
        self.assertTrue((staging / m.SIDECAR_STAGED_NAME).is_file())
        self.assertTrue((staging / m.INTERNAL_DIR / "python3.dll").is_file())
        self.assertTrue((staging / "Assets").is_dir())
        manifest = (staging / "AppxManifest.xml").read_text(encoding="utf-8")
        self.assertIn('Version="3.4.5.0"', manifest)

    def test_missing_ui_exe_raises(self) -> None:
        (self.target / m.UI_EXE).unlink()
        with self.assertRaises(FileNotFoundError):
            m.stage_payload(self.tmp / "staging", "3.4.5", target_dir=self.target)

    def test_missing_sidecar_raises(self) -> None:
        for exe in self.target.glob(m.SIDECAR_GLOB):
            exe.unlink()
        with self.assertRaises(FileNotFoundError):
            m.stage_payload(self.tmp / "staging", "3.4.5", target_dir=self.target)

    def test_staging_dir_is_reset(self) -> None:
        staging = self.tmp / "staging"
        staging.mkdir()
        stale = staging / "stale.txt"
        stale.write_text("old", encoding="utf-8")
        m.stage_payload(staging, "3.4.5", target_dir=self.target)
        self.assertFalse(stale.exists())


if __name__ == "__main__":
    unittest.main()
