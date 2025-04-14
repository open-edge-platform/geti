# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from unittest.mock import patch
from zipfile import ZipFile

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from job.entities.exceptions import SignatureKeysNotFound, SignatureVerificationFailed
from job.entities.zip_archive import PublicKeyBytes, SignatureBytes
from job.usecases.signature_usecase import SignatureUseCaseCertManager, SignatureUseCaseHelper, SignatureUseCaseKMS

DUMMY_SIGNATURE_BYTES = b"dummy_signature_bytes"
DUMMY_PUBLIC_KEY_BYTES = b"dummy_public_key_data"
PRIVATE_KEY_EC_PEM_STR = (
    ec.generate_private_key(ec.SECP384R1())
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf8")
)


class TestProjectZip:
    def __init__(self, local_zip_path: str):
        self.local_zip_path = local_zip_path
        with ZipFile(local_zip_path, "w") as zipfile:
            zipfile.writestr("data", b"data")
        with open(local_zip_path, mode="rb") as project_zip_file:
            self.zip_file_bytes = project_zip_file.read()

    def cleanup(self) -> None:
        os.remove(self.local_zip_path)


@pytest.fixture
def fxt_test_project_zip(request):
    local_zip_path = "test_project.zip"
    test_zip = TestProjectZip(local_zip_path=local_zip_path)
    request.addfinalizer(lambda: test_zip.cleanup())
    yield test_zip


@pytest.fixture
def fxt_public_key_bytes():
    private_key = serialization.load_pem_private_key(
        data=PRIVATE_KEY_EC_PEM_STR.encode(),
        password=None,
        backend=default_backend(),
        unsafe_skip_rsa_key_validation=True,
    )
    yield private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


@pytest.mark.ProjectIEMsComponent
class TestSignatureUseCaseCertManager:
    @patch.dict(
        os.environ,
        {"SIGNING_IE_PRIVKEY": PRIVATE_KEY_EC_PEM_STR, "FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT": "True"},
    )
    def test_sign_and_verify_external_key(self, fxt_test_project_zip, fxt_public_key_bytes) -> None:
        # Arrange
        signature_use_case = SignatureUseCaseCertManager()
        project_zip = fxt_test_project_zip
        signature_with_internal_key = signature_use_case.generate_signature(data=project_zip.zip_file_bytes)

        external_privkey_1 = ec.generate_private_key(ec.SECP384R1())
        external_privkey_2 = ec.generate_private_key(ec.SECP384R1())
        external_pubkey_1_bytes = PublicKeyBytes(
            external_privkey_1.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
        external_pubkey_2_bytes = PublicKeyBytes(
            external_privkey_2.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
        signature_with_external_key_1 = SignatureBytes(
            external_privkey_1.sign(
                data=signature_use_case.digest_data(project_zip.zip_file_bytes),
                signature_algorithm=ec.ECDSA(signature_use_case._hashing_algorithm),
            )
        )
        signature_with_external_key_2 = SignatureBytes(
            external_privkey_2.sign(
                data=signature_use_case.digest_data(project_zip.zip_file_bytes),
                signature_algorithm=ec.ECDSA(signature_use_case._hashing_algorithm),
            )
        )

        # Act & Assert
        # Check that signature can only be verified with the correct public key
        signature_use_case.verify(data=project_zip.zip_file_bytes, signature=signature_with_internal_key)
        with pytest.raises(SignatureVerificationFailed):
            signature_use_case.verify(data=project_zip.zip_file_bytes, signature=signature_with_external_key_1)
        signature_use_case.verify(
            data=project_zip.zip_file_bytes,
            signature=signature_with_external_key_1,
            public_key=external_pubkey_1_bytes,
        )
        with pytest.raises(SignatureVerificationFailed):
            signature_use_case.verify(
                data=project_zip.zip_file_bytes,
                signature=signature_with_external_key_1,
                public_key=external_pubkey_2_bytes,
            )
        signature_use_case.verify(
            data=project_zip.zip_file_bytes,
            signature=signature_with_external_key_2,
            public_key=external_pubkey_2_bytes,
        )
        with pytest.raises(SignatureVerificationFailed):
            signature_use_case.verify(
                data=project_zip.zip_file_bytes,
                signature=signature_with_external_key_2,
                public_key=external_pubkey_1_bytes,
            )

    @patch.dict(os.environ, {"SIGNING_IE_PRIVKEY": PRIVATE_KEY_EC_PEM_STR})
    def test_sign_and_verify_internal_key(self, fxt_test_project_zip, fxt_public_key_bytes) -> None:
        # Arrange
        signature_use_case = SignatureUseCaseCertManager()
        project_zip = fxt_test_project_zip
        signature_with_internal_key = signature_use_case.generate_signature(data=project_zip.zip_file_bytes)

        external_privkey = ec.generate_private_key(ec.SECP384R1())
        external_pubkey_bytes = PublicKeyBytes(
            external_privkey.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
        signature_with_external_key = SignatureBytes(
            external_privkey.sign(
                data=signature_use_case.digest_data(project_zip.zip_file_bytes),
                signature_algorithm=ec.ECDSA(signature_use_case._hashing_algorithm),
            )
        )

        # Act & Assert
        # Check that only the signatures signed with the internal key can be verified
        signature_use_case.verify(data=project_zip.zip_file_bytes, signature=signature_with_internal_key)
        with pytest.raises(SignatureVerificationFailed):
            signature_use_case.verify(
                data=project_zip.zip_file_bytes,
                signature=signature_with_external_key,
                public_key=external_pubkey_bytes,
            )

    def test_signature_keys_not_found(self) -> None:
        with pytest.raises(SignatureKeysNotFound):
            SignatureUseCaseCertManager()


@pytest.mark.ProjectIEMsComponent
class TestSignatureUseCaseHelper:
    @pytest.mark.parametrize(
        "key_source, signature_use_case_type",
        [
            ("kms", SignatureUseCaseKMS),
            ("cert-manager", SignatureUseCaseCertManager),
        ],
    )
    @patch.dict(
        os.environ,
        {"SIGNING_IE_PRIVKEY": PRIVATE_KEY_EC_PEM_STR, "KMS_PRIVKEY_ID": "dummy_id", "KMS_PUBKEY_ID": "dummy_id"},
    )
    def test_signature_use_case_helper(self, key_source, signature_use_case_type) -> None:
        # Arrange
        os.environ["PROJECT_IMPORT_KEY_SOURCE"] = key_source

        # Act
        signature_use_case = SignatureUseCaseHelper.get_signature_use_case()

        # Assert
        assert type(signature_use_case) is signature_use_case_type

    def test_signature_use_case_helper_not_supported(self) -> None:
        # Arrange
        os.environ["PROJECT_IMPORT_KEY_SOURCE"] = "unsupported-source"

        # Act & Assert
        with pytest.raises(ValueError):
            SignatureUseCaseHelper.get_signature_use_case()
