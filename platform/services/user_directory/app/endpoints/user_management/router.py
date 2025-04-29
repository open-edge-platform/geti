# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from fastapi import APIRouter

from common.utils import API_BASE_PATTERN

users_router = APIRouter(prefix=f"{API_BASE_PATTERN}/users", tags=["users"])
organization_router = APIRouter(prefix=f"{API_BASE_PATTERN}/organizations", tags=["organizations"])
