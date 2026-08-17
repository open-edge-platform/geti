# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

import pytest
from fastapi import status

from app.api.dependencies import get_ice_servers, get_webrtc_manager
from app.models.webrtc import Answer, InputData, Offer
from app.webrtc.manager import WebRTCManager


@pytest.fixture
def fxt_webrtc_manager(fxt_app):
    webrtc_manager = MagicMock(spec=WebRTCManager)
    fxt_app.dependency_overrides[get_webrtc_manager] = lambda: webrtc_manager
    return webrtc_manager


@pytest.fixture
def fxt_offer() -> Offer:
    return Offer(sdp="test_sdp", type="offer", webrtc_id="test_id")


@pytest.fixture
def fxt_answer() -> Answer:
    return Answer(sdp="test_sdp", type="answer")


@pytest.fixture
def fxt_input_data() -> InputData:
    return InputData(webrtc_id="test_id", conf_threshold=0.5)


class TestWebRTCEndpoints:
    def test_create_webrtc_offer_success(self, fxt_client, fxt_webrtc_manager, fxt_offer, fxt_answer):
        fxt_webrtc_manager.handle_offer.return_value = fxt_answer
        resp = fxt_client.post("/api/webrtc/offer", json=fxt_offer.model_dump(mode="json"))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == fxt_answer.model_dump()
        fxt_webrtc_manager.handle_offer.assert_called_once()

    def test_create_webrtc_offer_failure(self, fxt_client, fxt_webrtc_manager, fxt_offer):
        fxt_webrtc_manager.handle_offer.side_effect = Exception("fail")
        resp = fxt_client.post("/api/webrtc/offer", json=fxt_offer.model_dump(mode="json"))
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert resp.json()["detail"] == "Failed to process WebRTC offer"
        fxt_webrtc_manager.handle_offer.assert_called_once()

    def test_create_webrtc_offer_invalid_payload(self, fxt_client):
        resp = fxt_client.post("/api/webrtc/offer", json={"sdp": 123})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_webrtc_input_hook_success(self, fxt_client, fxt_webrtc_manager, fxt_input_data):
        resp = fxt_client.post("/api/webrtc/input_hook", json=fxt_input_data.model_dump(mode="json"))
        assert resp.status_code == status.HTTP_200_OK
        fxt_webrtc_manager.set_input.assert_called_once()

    def test_webrtc_input_hook_invalid_payload(self, fxt_client, fxt_webrtc_manager):
        resp = fxt_client.post("/api/webrtc/input_hook", json={"wrong": "field"})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_get_webrtc_config_empty(self, fxt_app, fxt_client):
        fxt_app.dependency_overrides[get_ice_servers] = lambda: []  # noqa: PIE807
        resp = fxt_client.get("/api/webrtc/config")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {"iceServers": []}

    def test_get_webrtc_config_with_servers(self, fxt_app, fxt_client):
        fxt_app.dependency_overrides[get_ice_servers] = lambda: [
            {"urls": "turn:192.168.1.100:443?transport=tcp", "username": "user", "credential": "password"},
            {"urls": "stun:stun.example.com:3478"},
        ]
        resp = fxt_client.get("/api/webrtc/config")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {
            "iceServers": [
                {"urls": "turn:192.168.1.100:443?transport=tcp", "username": "user", "credential": "password"},
                {"urls": "stun:stun.example.com:3478", "username": None, "credential": None},
            ]
        }


class TestWebRTCInputValidationSecurity:
    """Security regression tests for H4 and H5 (PR1)."""

    @pytest.mark.parametrize("type_value", ["invalid", "", "OFFER", "Answer", "rollback_extra", "null", "1"])
    def test_offer_invalid_type_rejected(self, fxt_client, type_value):
        """Type values outside the Literal enum must be rejected with 422, not cause 500."""
        payload = {"sdp": "v=0\r\n", "type": type_value, "webrtc_id": "id"}
        resp = fxt_client.post("/api/webrtc/offer", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_offer_empty_sdp_rejected(self, fxt_client):
        """sdp requires at least 1 character (Field(min_length=1))."""
        payload = {"sdp": "", "type": "offer", "webrtc_id": "id"}
        resp = fxt_client.post("/api/webrtc/offer", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_offer_library_value_error_returns_400_not_500(self, fxt_client, fxt_webrtc_manager):
        """ValueError from downstream library (e.g. aiortc) must map to 400, not 500."""
        fxt_webrtc_manager.handle_offer.side_effect = ValueError("'type' must be in ['offer', ...]")
        payload = {"sdp": "v=0\r\n", "type": "offer", "webrtc_id": "id"}
        resp = fxt_client.post("/api/webrtc/offer", json=payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["detail"] == "Invalid WebRTC offer parameters."

    def test_offer_generic_exception_still_returns_500(self, fxt_client, fxt_webrtc_manager):
        """Non-ValueError exceptions must still result in 500, not silently swallowed."""
        fxt_webrtc_manager.handle_offer.side_effect = RuntimeError("unexpected")
        payload = {"sdp": "v=0\r\n", "type": "offer", "webrtc_id": "id"}
        resp = fxt_client.post("/api/webrtc/offer", json=payload)
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_input_hook_conf_threshold_bool_coercion_rejected(self, fxt_client):
        """Boolean False must NOT be silently coerced to 0.0 (StrictFloat)."""
        resp = fxt_client.post("/api/webrtc/input_hook", json={"webrtc_id": "id", "conf_threshold": False})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_input_hook_conf_threshold_float_accepted(self, fxt_client, fxt_webrtc_manager):
        """A proper float value must still be accepted."""
        resp = fxt_client.post("/api/webrtc/input_hook", json={"webrtc_id": "id", "conf_threshold": 0.75})
        assert resp.status_code == status.HTTP_200_OK
