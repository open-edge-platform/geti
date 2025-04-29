# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from fastapi import APIRouter

products_router = APIRouter(prefix="/products")

orgs_router = APIRouter(prefix="/organizations")

internal_router = APIRouter(prefix="/internal/tasks")
