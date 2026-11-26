#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from model_api.adapters.ovms_adapter import OVMSAdapter


class TestParseModelArg:
    """Test cases for the parse_model_arg function."""

    def test_valid_url_with_version(self):
        """Test parsing a valid URL with version specified."""
        target_model = "http://localhost:8000/v2/models/my_model/versions/123"
        service_url, model_name, version = OVMSAdapter.parse_model_arg(target_model)

        assert service_url == "http://localhost:8000"
        assert model_name == "my_model"
        assert version == "123"

    def test_valid_url_without_version(self):
        """Test parsing a valid URL without version specified."""
        target_model = "http://localhost:8000/v2/models/345$%^!@#$model"
        service_url, model_name, version = OVMSAdapter.parse_model_arg(target_model)

        assert service_url == "http://localhost:8000"
        assert model_name == "345$%^!@#$model"
        assert version == ""

    def test_valid_url_with_trailing_slash(self):
        """Test parsing a valid URL with trailing slash."""
        target_model = "http://localhost:8000/v2/models/my_model/"
        service_url, model_name, version = OVMSAdapter.parse_model_arg(target_model)

        assert service_url == "http://localhost:8000"
        assert model_name == "my_model"
        assert version == ""

    def test_valid_url_with_version_and_trailing_slash(self):
        """Test parsing a valid URL with version and trailing slash."""
        target_model = "http://localhost:8000/v2/models/my_model/versions/456/"
        service_url, model_name, version = OVMSAdapter.parse_model_arg(target_model)

        assert service_url == "http://localhost:8000"
        assert model_name == "my_model"
        assert version == "456"

    def test_valid_url_https(self):
        """Test parsing a valid HTTPS URL."""
        target_model = "https://example.com:8080/v2/models/test_model/versions/1"
        service_url, model_name, version = OVMSAdapter.parse_model_arg(target_model)

        assert service_url == "https://example.com:8080"
        assert model_name == "test_model"
        assert version == "1"

    def test_valid_scheme_less_url_with_version(self):
        """Test parsing a valid scheme-less URL with version specified."""
        target_model = "localhost:8000/v2/models/my_model/versions/123"
        service_url, model_name, version = OVMSAdapter.parse_model_arg(target_model)

        assert service_url == "localhost:8000"
        assert model_name == "my_model"
        assert version == "123"

    @pytest.mark.parametrize(
        ("target_model", "description"),
        [
            ("http://localhost:8000/models/my_model", "missing v2/models path"),
            ("http://localhost:8000/v2/models/my_model/version/123", "wrong versions format"),
            ("http://localhost:8000/v2/models//versions/123", "empty model name"),
            ("http://localhost:8000/v2/models/", "no model name"),
            ("http://localhost:8000/v2", "incomplete URL"),
            ("http://localhost:8000/v2/models/my_model/versions/latest", "non-numeric version"),
            ("http://localhost:8000/v2/models/my_model/extra/path", "extra path"),
            ("http://localhost:8000/v2/models/my_model/versions/", "no version specified"),
            ("", "empty"),
        ],
    )
    def test_invalid_url_formats(self, target_model, description):
        """Test parsing various invalid URL formats."""
        with pytest.raises(ValueError, match="invalid --model option format"):
            OVMSAdapter.parse_model_arg(target_model)
