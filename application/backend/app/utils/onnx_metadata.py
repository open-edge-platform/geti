# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Lightweight reader for the metadata properties embedded in ONNX model files.

The ONNX format is a protobuf-encoded ``ModelProto`` message in which the metadata properties are a tiny
field sitting next to the (potentially huge) computational graph and its weights. Rather than deserializing
the whole model, this module walks the top-level protobuf fields and seeks over everything but the metadata.
"""

from collections.abc import Iterable, Iterator
from io import BytesIO
from os import SEEK_CUR
from pathlib import Path
from typing import BinaryIO

# Protobuf field numbers within the ONNX `ModelProto` and `StringStringEntryProto` messages
_METADATA_PROPS_FIELD = 14
_ENTRY_KEY_FIELD = 1
_ENTRY_VALUE_FIELD = 2


def read_onnx_metadata_attrs(model_path: Path, keys: Iterable[str]) -> dict[str, str]:
    """
    Read the requested metadata properties from an ONNX model file.

    Args:
        model_path (Path): Path to the ``.onnx`` model file.
        keys (Iterable[str]): Metadata keys to look for, e.g. ``["model_info confidence_threshold"]``.

    Returns:
        dict[str, str]: The requested keys mapped to their values. Keys absent from the model are omitted,
            so the result may be empty.

    Raises:
        OSError: If the model file cannot be read.
        ValueError: If the file is not a valid protobuf message.
    """
    wanted = set(keys)
    found: dict[str, str] = {}
    with model_path.open("rb") as stream:
        for _, entry in _iter_protobuf_fields(stream, {_METADATA_PROPS_FIELD}):
            fields = dict(_iter_protobuf_fields(BytesIO(entry), {_ENTRY_KEY_FIELD, _ENTRY_VALUE_FIELD}))
            key = fields.get(_ENTRY_KEY_FIELD, b"").decode()
            if key in wanted:
                found[key] = fields.get(_ENTRY_VALUE_FIELD, b"").decode()
                if len(found) == len(wanted):
                    break
    return found


def _read_varint(stream: BinaryIO) -> int | None:
    """Read a protobuf base-128 varint from the stream, or return None if the stream is exhausted."""
    value = shift = 0
    while chunk := stream.read(1):
        value |= (chunk[0] & 0x7F) << shift
        if not chunk[0] & 0x80:
            return value
        shift += 7
    return None


def _iter_protobuf_fields(stream: BinaryIO, field_numbers: set[int]) -> Iterator[tuple[int, bytes]]:
    """
    Walk the top-level fields of a protobuf message, yielding the payload of the requested ones.

    Fields that were not requested are seeked over instead of being read into memory, which makes it cheap
    to pull a tiny field out of a huge message.

    Args:
        stream (BinaryIO): Seekable stream positioned at the start of the encoded message.
        field_numbers (set[int]): Numbers of the length-delimited fields to yield.

    Yields:
        tuple[int, bytes]: Field number and raw payload of each requested field.

    Raises:
        ValueError: If the message contains an unsupported protobuf wire type.
    """
    while (tag := _read_varint(stream)) is not None:
        field_number, wire_type = tag >> 3, tag & 0x07
        match wire_type:
            case 0:  # varint
                _read_varint(stream)
            case 1:  # 64-bit
                stream.seek(8, SEEK_CUR)
            case 2:  # length-delimited
                length = _read_varint(stream) or 0
                if field_number in field_numbers:
                    yield field_number, stream.read(length)
                else:
                    stream.seek(length, SEEK_CUR)
            case 5:  # 32-bit
                stream.seek(4, SEEK_CUR)
            case _:
                raise ValueError(f"Unsupported protobuf wire type {wire_type}")
