# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Self-signed TLS certificate provisioning for the local HTTPS server."""

import contextlib
import datetime
import ipaddress
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from loguru import logger

_VALIDITY_DAYS = 3650
_KEY_FILE_MODE = 0o600


def _write_private_key(key_path: Path, data: bytes) -> None:
    """Write an unencrypted private key readable only by its owner.

    The file is created with restrictive permissions rather than relaxed afterwards, so
    the key is never briefly world-readable. POSIX modes are advisory on Windows, where
    the key is protected by the ACL of the data directory instead.

    Args:
        key_path: Destination of the private key.
        data: PEM-encoded private key bytes.
    """
    descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _KEY_FILE_MODE)
    with open(descriptor, "wb") as key_file:
        # O_CREAT leaves the mode of a pre-existing file untouched, so narrow it explicitly.
        with contextlib.suppress(OSError):
            key_path.chmod(_KEY_FILE_MODE)
        key_file.write(data)


def generate_self_signed_cert(cert_path: Path, key_path: Path) -> None:
    """Write a new self-signed certificate and private key for localhost.

    Args:
        cert_path: Destination of the PEM-encoded certificate.
        key_path: Destination of the PEM-encoded, unencrypted private key.
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=_VALIDITY_DAYS))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                    x509.IPAddress(ipaddress.ip_address("::1")),
                ]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    _write_private_key(
        key_path,
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ),
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def ensure_certs_exist(cert_path: Path, key_path: Path) -> None:
    """Generate a self-signed certificate pair unless it is already present.

    The server always serves HTTPS, so it cannot start without a certificate. Source
    installations that launch ``app/main.py`` directly never run the ``gen-certs``
    recipe, so provision the pair here instead of failing to bind.

    Args:
        cert_path: Expected location of the PEM-encoded certificate.
        key_path: Expected location of the PEM-encoded private key.
    """
    if cert_path.exists() and key_path.exists():
        return

    logger.info("No complete TLS certificate/key pair found; generating a self-signed one at {}", cert_path.parent)
    generate_self_signed_cert(cert_path, key_path)
    logger.info("Self-signed TLS certificate generated. Browsers will warn about it on first connection.")
