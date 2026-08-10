# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import stat
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes

from app.core.certs import ensure_certs_exist


def _public_key_pem(public_key: PublicKeyTypes) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def test_ensure_certs_exist_generates_usable_pair(tmp_path: Path) -> None:
    cert_path = tmp_path / "certs" / "localhost.pem"
    key_path = tmp_path / "certs" / "localhost-key.pem"

    assert ensure_certs_exist(cert_path, key_path) is True

    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    assert cert.subject.rfc4514_string() == "CN=localhost"

    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert "localhost" in san.get_values_for_type(x509.DNSName)

    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    assert key.key_size == 2048


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes are not enforced on Windows")
def test_ensure_certs_exist_writes_an_owner_only_key(tmp_path: Path) -> None:
    cert_path = tmp_path / "certs" / "localhost.pem"
    key_path = tmp_path / "certs" / "localhost-key.pem"

    ensure_certs_exist(cert_path, key_path)

    assert stat.S_IMODE(key_path.stat().st_mode) == 0o600


def test_ensure_certs_exist_reuses_existing_pair(tmp_path: Path) -> None:
    cert_path = tmp_path / "certs" / "localhost.pem"
    key_path = tmp_path / "certs" / "localhost-key.pem"
    ensure_certs_exist(cert_path, key_path)
    original_cert = cert_path.read_bytes()
    original_key = key_path.read_bytes()

    assert ensure_certs_exist(cert_path, key_path) is False
    assert cert_path.read_bytes() == original_cert
    assert key_path.read_bytes() == original_key


def test_ensure_certs_exist_regenerates_when_key_is_missing(tmp_path: Path) -> None:
    cert_path = tmp_path / "certs" / "localhost.pem"
    key_path = tmp_path / "certs" / "localhost-key.pem"
    ensure_certs_exist(cert_path, key_path)
    original_cert = cert_path.read_bytes()
    key_path.unlink()

    assert ensure_certs_exist(cert_path, key_path) is True
    assert key_path.exists()
    assert cert_path.read_bytes() != original_cert

    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    assert _public_key_pem(cert.public_key()) == _public_key_pem(key.public_key())
