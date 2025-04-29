# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Pydantic models for project import"""

from pydantic import BaseModel


class ImportOperation(BaseModel):
    file_id: str
    project_name: str | None = None
