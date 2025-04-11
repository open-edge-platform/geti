# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
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
