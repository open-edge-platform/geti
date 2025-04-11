# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from fastapi import FastAPI
from grpc_interfaces.account_service.client import AccountServiceClient

from models.organization import Organization
from models.user import User
from models.workspace import Workspace
from routers import admin, onboarding

from communication.account_service.account_service import OrganizationRepo, UserRepo, WorkspaceRepo

# Inject account_service backend for Organization/User models
account_service_client = AccountServiceClient(metadata_getter=lambda: ())
Organization.repo = OrganizationRepo(account_service_client)
User.repo = UserRepo(account_service_client)
Workspace.repo = WorkspaceRepo(account_service_client)


app = FastAPI()
app.include_router(admin.router)
app.include_router(onboarding.router)
