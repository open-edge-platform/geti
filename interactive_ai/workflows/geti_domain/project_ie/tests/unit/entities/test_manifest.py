# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime

import pytest

from job.entities import Manifest


@pytest.fixture
def fxt_manifest():
    yield Manifest(version="1.0", export_date=datetime.utcfromtimestamp(0), min_id="00000000000000000000000f")


@pytest.fixture
def fxt_encoded_manifest():
    yield b'{"version": "1.0", "export_date": {"$date": "1970-01-01T00:00:00Z"}, "min_id": "00000000000000000000000f"}'


@pytest.mark.ProjectIEMsComponent
class TestManifest:
    def test_encode(self, fxt_manifest, fxt_encoded_manifest) -> None:
        encoded_manifest = fxt_manifest.encode()
        assert encoded_manifest == fxt_encoded_manifest

    def test_decode(self, fxt_manifest, fxt_encoded_manifest) -> None:
        decoded_manifest = Manifest.decode(fxt_encoded_manifest)
        assert decoded_manifest == fxt_manifest
