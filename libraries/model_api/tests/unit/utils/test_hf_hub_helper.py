# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
from model_api.utils.hf_hub_helper import find_model_file


def test_find_model_file_with_filename(request):
    d = Path(request.fspath).parent / "test_model_dir"
    d.mkdir(exist_ok=True)
    (d / "model.xml").touch()
    try:
        result = find_model_file(d, filename="model.xml")
        assert result == d / "model.xml"
    finally:
        (d / "model.xml").unlink()
        d.rmdir()


def test_find_model_file_not_found(request):
    d = Path(request.fspath).parent / "test_model_dir2"
    d.mkdir(exist_ok=True)
    try:
        with pytest.raises(FileNotFoundError, match="Specified model file not found"):
            find_model_file(d, filename="nonexistent.xml")
    finally:
        d.rmdir()


def test_find_single_xml(request):
    d = Path(request.fspath).parent / "test_model_dir3"
    d.mkdir(exist_ok=True)
    (d / "model.xml").touch()
    try:
        result = find_model_file(d)
        assert result == d / "model.xml"
    finally:
        (d / "model.xml").unlink()
        d.rmdir()


def test_find_single_onnx(request):
    d = Path(request.fspath).parent / "test_model_dir4"
    d.mkdir(exist_ok=True)
    (d / "model.onnx").touch()
    try:
        result = find_model_file(d)
        assert result == d / "model.onnx"
    finally:
        (d / "model.onnx").unlink()
        d.rmdir()


def test_find_multiple_xml_raises(request):
    d = Path(request.fspath).parent / "test_model_dir5"
    d.mkdir(exist_ok=True)
    (d / "a.xml").touch()
    (d / "b.xml").touch()
    try:
        with pytest.raises(ValueError, match="Multiple OpenVINO IR model files"):
            find_model_file(d)
    finally:
        (d / "a.xml").unlink()
        (d / "b.xml").unlink()
        d.rmdir()


def test_find_multiple_onnx_raises(request):
    d = Path(request.fspath).parent / "test_model_dir6"
    d.mkdir(exist_ok=True)
    (d / "a.onnx").touch()
    (d / "b.onnx").touch()
    try:
        with pytest.raises(ValueError, match="Multiple ONNX model files"):
            find_model_file(d)
    finally:
        (d / "a.onnx").unlink()
        (d / "b.onnx").unlink()
        d.rmdir()


def test_find_no_model_files(request):
    d = Path(request.fspath).parent / "test_model_dir7"
    d.mkdir(exist_ok=True)
    (d / "readme.txt").touch()
    try:
        with pytest.raises(FileNotFoundError, match="No model files"):
            find_model_file(d)
    finally:
        (d / "readme.txt").unlink()
        d.rmdir()
