# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from service.inference_manager import InferenceManager


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.create")
@patch("service.inference_manager.InferenceService.get")
async def test_create_inference(mock_get, mock_create):
    with patch("asyncio.sleep", return_value=None):
        mock_get.side_effect = [
            None,
            MagicMock(status={"conditions": []}),
            MagicMock(status={"conditions": [{"type": "Not Ready"}]}),
            MagicMock(status={"conditions": [{"type": "Ready", "status": "True"}]}),
        ]

        manager = InferenceManager()
        await manager.create_inference("test-name", "test-namespace", "test-storage", "test-path")
        mock_create.assert_called_once()
        assert mock_get.call_count > 1


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.create")
@patch("service.inference_manager.InferenceService.get")
async def test_create_inference_fail(mock_get, mock_create):
    with patch("asyncio.sleep", return_value=None):
        manager = InferenceManager()
        with pytest.raises(RuntimeError):
            await manager.create_inference("test-name", "test-namespace", "test-storage", "test-path")


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.delete")
@patch("service.inference_manager.InferenceService.get")
async def test_remove_inference(mock_get, mock_delete):
    with patch("asyncio.sleep", return_value=None):
        mock_get.side_effect = [AsyncMock(), None]

        manager = InferenceManager()
        await manager.remove_inference("test-name", "test-namespace")


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.delete")
@patch("service.inference_manager.InferenceService.get")
async def test_remove_inference_fail(mock_get, mock_delete):
    with patch("asyncio.sleep", return_value=None):
        manager = InferenceManager()
        with pytest.raises(RuntimeError):
            await manager.remove_inference("test-name", "test-namespace")


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.get", return_value=None)
async def test_remove_inference_not_found(mock_get):
    with patch("asyncio.sleep", return_value=None):
        manager = InferenceManager()
        with pytest.raises(RuntimeError):
            await manager.remove_inference("test-name", "test-namespace")


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.list")
async def test_list_inference(mock_list):
    mock_list.return_value = "model1 model2"

    manager = InferenceManager()
    result = await manager.list_inference("test-namespace")
    assert result == "model1 model2"


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.get")
async def test_get_inference(mock_get):
    mock_get.return_value = MagicMock(status={"conditions": [{"type": "Ready", "status": "True"}]})

    manager = InferenceManager()
    result = await manager.get_inference("test-name", "test-namespace")
    assert result.status["conditions"][0]["type"] == "Ready"
    assert result.status["conditions"][0]["status"] == "True"


@pytest.mark.asyncio
@patch("service.inference_manager.InferenceService.get")
async def test_get_inference_not_found(mock_get):
    mock_get.return_value = None

    manager = InferenceManager()
    result = await manager.get_inference("test-name", "test-namespace")
    assert result is None
