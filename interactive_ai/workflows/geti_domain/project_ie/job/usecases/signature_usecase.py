# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module is responsible for generating and verifying signatures of import/export zip files.
"""

import abc
import logging
import os
from collections.abc import Iterable
from enum import Enum

import boto3
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider

from job.entities.exceptions import SignatureKeysNotFound, SignatureVerificationFailed
from job.entities.zip_archive import PublicKeyBytes, SignatureBytes

logger = logging.getLogger(__name__)

KEY_SOURCE_ENV_NAME = "PROJECT_IMPORT_KEY_SOURCE"
KMS_PUBKEY_ENV_NAME = "KMS_PUBKEY_ID"
KMS_PRIVKEY_ENV_NAME = "KMS_PRIVKEY_ID"
CERT_MANAGER_PRIVKEY_ENV_NAME = "SIGNING_IE_PRIVKEY"


class KeySource(Enum):
    CERT_MANAGER = "cert-manager"
    KMS = "kms"


class SignatureUseCase(abc.ABC):
    """
    This class is responsible for generating and verifying signatures of import/export zip files.
    """

    _hashing_algorithm = hashes.SHA384()

    @classmethod
    def digest_data(cls, data: bytes | Iterable[bytes]) -> bytes:
        """
        Computes the digest (hash) of the provided data.

        :param data: the input data to be hashed. This can be either a bytes object or an Iterable of bytes
        :return: the hash digest of the input data
        """
        hasher = hashes.Hash(cls._hashing_algorithm)
        if isinstance(data, Iterable) and not isinstance(data, bytes):
            for chunk in data:
                hasher.update(chunk)
            return hasher.finalize()
        hasher.update(data)
        return hasher.finalize()

    @property
    def public_key_bytes(self) -> PublicKeyBytes:
        """Returns the public key as bytes (DER encoded)."""
        raise NotImplementedError

    @abc.abstractmethod
    def generate_signature(self, data: bytes | Iterable[bytes]) -> SignatureBytes:
        """
        Generates the digital signature for the given binary data.

        :param data: binary data to sign
        :return: the signature as bytes
        """
        raise NotImplementedError

    @abc.abstractmethod
    def verify(self, data: bytes | Iterable[bytes], signature: bytes, public_key: PublicKeyBytes | None = None) -> None:
        """
        Verifies that the data has not been manipulated by checking its digital signature.

        :param data: the binary data to verify
        :param signature: the signature to check
        :param public_key: external public key to use for the verification (DER encoded)
        :raises SignatureVerificationFailed: if the signature does not match
        """
        raise NotImplementedError


class SignatureUseCaseCertManager(SignatureUseCase):
    """
    This class is responsible for generating and verifying signatures through Cert-Manager keys.
    """

    def __init__(self) -> None:
        # get the latest private key from the env vars (stored as str)
        try:
            internal_private_key = os.environ[CERT_MANAGER_PRIVKEY_ENV_NAME].encode()
            self._private_key = serialization.load_pem_private_key(
                data=internal_private_key,
                password=None,
                backend=default_backend(),
                unsafe_skip_rsa_key_validation=True,
            )
        except KeyError:
            logger.exception("Missing signing keys from cert-manager. Please check that env vars are set correctly.")
            raise SignatureKeysNotFound

    @property
    def public_key_bytes(self) -> PublicKeyBytes:
        return PublicKeyBytes(
            self._get_public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    def _get_public_key(self, public_key: PublicKeyBytes | None = None) -> ec.EllipticCurvePublicKey:
        """
        Returns the public key for signature verification purposes.

        :param public_key: public key binary (DER encoded) to use for the verification.
            By default, the internal certificate file is used.
        :return: the public key
        """
        if public_key is not None:
            logger.info("Loading public key from archive.")
            return serialization.load_der_public_key(data=public_key, backend=default_backend())  # type: ignore
        logger.info("Loading public key from private key.")
        return self._private_key.public_key()  # type: ignore

    def generate_signature(self, data: bytes | Iterable[bytes]) -> SignatureBytes:
        digest = self.digest_data(data)
        if not isinstance(self._private_key, ec.EllipticCurvePrivateKey):
            raise ValueError(
                "Invalid private key type. "
                "The private key must be an EllipticCurvePrivateKey, "
                f"but found '{type(self._private_key).__name__}'."
            )
        return SignatureBytes(
            self._private_key.sign(data=digest, signature_algorithm=ec.ECDSA(self._hashing_algorithm))
        )

    def verify(self, data: bytes | Iterable[bytes], signature: bytes, public_key: PublicKeyBytes | None = None) -> None:
        # TODO CVS-135214: verify with expired keys once key rotation is implemented
        internal_pubkey = self._get_public_key()
        digest = self.digest_data(data)
        # 1. Verify signature against internal public key
        try:
            internal_pubkey.verify(
                signature=signature, data=digest, signature_algorithm=ec.ECDSA(self._hashing_algorithm)
            )
            return
        except InvalidSignature:
            # 2. Verify signature against external public key if internal key fails
            if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT):
                logger.info("Verifying imported project signature with external public key.")
                external_pubkey = self._get_public_key(public_key=public_key)
                try:
                    external_pubkey.verify(
                        signature=signature, data=digest, signature_algorithm=ec.ECDSA(self._hashing_algorithm)
                    )
                    return
                except InvalidSignature:
                    logger.exception("Signature verification failed on external public key.")
                    raise SignatureVerificationFailed
            logger.exception("Signature verification failed on internal public key.")
            raise SignatureVerificationFailed


class SignatureUseCaseKMS(SignatureUseCase):
    """
    This class is responsible for generating and verifying signatures through AWS KMS.
    """

    def __init__(self):
        try:
            self._public_key_id = os.environ[KMS_PUBKEY_ENV_NAME]
            self._private_key_id = os.environ[KMS_PRIVKEY_ENV_NAME]
        except KeyError:
            raise SignatureKeysNotFound
        self.client = boto3.client("kms")
        self.signing_algorithm = "ECDSA_SHA_384"

    @property
    def public_key_bytes(self) -> PublicKeyBytes:
        response = self.client.get_public_key(KeyId=self._public_key_id)
        return PublicKeyBytes(response["PublicKey"])

    def generate_signature(self, data: bytes | Iterable[bytes]) -> SignatureBytes:
        digest = self.digest_data(data)
        response: dict = self.client.sign(
            KeyId=self._private_key_id,
            Message=digest,
            MessageType="DIGEST",
            SigningAlgorithm=self.signing_algorithm,
        )
        return SignatureBytes(response["Signature"])

    def verify(self, data: bytes | Iterable[bytes], signature: bytes, public_key: PublicKeyBytes | None = None) -> None:
        """
        Verifies that the data has not been manipulated by checking its digital signature.

        :param data: the binary data to verify
        :param signature: the signature to check
        :param public_key: this attribute is ignored and not supported by this class
        :raises SignatureVerificationFailed: if the signature does not match
        """
        # TODO CCVS-135213: verify with expired keys once key rotation is implemented
        if public_key is not None:
            logger.warning("The external public key is ignored. Using public key stored in KMS.")
        digest = self.digest_data(data)
        response = self.client.verify(
            KeyId=self._public_key_id,
            Message=digest,
            MessageType="DIGEST",
            Signature=signature,
            SigningAlgorithm=self.signing_algorithm,
        )
        if not response["SignatureValid"]:
            raise SignatureVerificationFailed


class SignatureUseCaseHelper:
    @staticmethod
    def get_signature_use_case() -> SignatureUseCase:
        """
        Helper function to get the correct SignatureUseCase implementation.

        :return: a concrete SignatureUseCase
        :raises NotImplementedError: if the configured key source is not supported
        """
        key_source = KeySource(os.environ.get(KEY_SOURCE_ENV_NAME, KeySource.CERT_MANAGER.value))
        match key_source:
            case KeySource.KMS:
                return SignatureUseCaseKMS()
            case KeySource.CERT_MANAGER:
                return SignatureUseCaseCertManager()
            case _:
                raise NotImplementedError(f"Loading keys from `{key_source}` is not yet supported.")
