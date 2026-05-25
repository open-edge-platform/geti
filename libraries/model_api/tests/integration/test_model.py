#
# Copyright (C) 2020-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
from pathlib import Path

import numpy as np
import pytest
from model_api.models.model import Model

rng = np.random.default_rng(seed=42)
image = rng.integers(low=0, high=255, size=(640, 640, 3), dtype=np.uint8)


def test_model(path, device) -> None:
    """
    Test loading a model and performing inference on a random image.
    The test will pass if the model loads and runs without exceptions.
    """
    model = get_model(path, device=device)

    model(image)

    assert True


def pytest_generate_tests(metafunc):
    """Parametrize the 'path' fixture based on command-line options."""
    if "path" in metafunc.fixturenames:
        model_path = metafunc.config.getoption("model_path")
        author = metafunc.config.getoption("author")
        collection = metafunc.config.getoption("collection")

        paths = get_paths(model_path, author, collection)

        if not paths:
            pytest.skip("No model path provided via --model-path or --author/--collection")

        metafunc.parametrize("path", paths)


def get_paths(model_path, author, collection) -> list[str]:
    """
    Determine model paths based on command-line arguments.

    Priority:
    1. If --model-path is provided, use it (can be a file, directory, or Hugging Face path).
    2. If --author is provided (with optional --collection), fetch model paths from Hugging Face Hub.
    3. If neither is provided, return an empty list.
    """
    if model_path:
        if model_path.startswith("hf://"):
            return [model_path]

        path = Path(model_path)
        if path.is_file():
            return [model_path]

        if path.is_dir():
            return [str(p) for p in path.rglob("*.xml")]

        msg = f"Invalid model path: {model_path}, expected a file, directory, or Hugging Face path starting with hf://"
        raise ValueError(msg)

    if author:
        return get_model_paths_from_hf(author, collection)

    return []


def get_model(path: str, device: str) -> Model:
    """Load a model from a given path, which can be a local file/directory or a Hugging Face Hub repository."""
    if path.startswith("hf://"):
        return Model.from_pretrained(path[5:], device=device)

    return Model.create_model(path, device=device)


def get_model_paths_from_hf(author: str, collection: str | None = None) -> list[str]:
    """Fetch model paths from Hugging Face Hub based on author and optional collection in a format ''hf://{repo_id}''."""
    from huggingface_hub import HfApi, get_collection

    api = HfApi()

    if collection:
        return [
            f"hf://{item.item_id}"
            for item in get_collection(f"{author}/{collection}").items
            if item.item_type == "model"
        ]

    return [f"hf://{model.id}" for model in api.list_models(author=author)]
