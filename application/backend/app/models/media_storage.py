# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from pydantic import Field, model_validator

from .base import BaseValueObject


class MediaStorage(BaseValueObject):
    """Location of a media payload: either a file or a directory-backed layout."""

    root: Path = Field(description="Root path that stores this media payload.")
    entrypoint: Path | None = Field(
        default=None,
        description="Relative path inside root used as entrypoint for directory-backed media; "
        "None for single-file media.",
    )

    @property
    def is_directory(self) -> bool:
        return self.entrypoint is not None

    @property
    def effective_path(self) -> Path:
        return self.root / self.entrypoint if self.entrypoint is not None else self.root

    @model_validator(mode="after")
    def validate_entrypoint(self) -> "MediaStorage":
        # Keep storage declarative: don't hit filesystem, just enforce shape.
        if self.entrypoint is not None and self.entrypoint.is_absolute():
            raise ValueError("entrypoint must be relative to root")
        return self
