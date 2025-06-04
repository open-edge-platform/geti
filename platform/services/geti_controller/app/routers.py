# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from fastapi import APIRouter

platform_router = APIRouter(prefix="/platform", tags=["Platform"])
