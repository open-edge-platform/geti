# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

account_service_grpc_gateway_address = os.getenv("ACCOUNT_SERVICE_GRPC_GATEWAY_ADDRESS", "127.0.0.1:5002")
s3_public_address = os.getenv("S3_PUBLIC_ADDRESS", "127.0.0.1:8333")
# noinspection HttpUrlsUsage
protocol = "http://"
api_v1_prefix = "/api/v1"

FF_MANAGE_USERS = os.getenv("FEATURE_FLAG_MANAGE_USERS", False)
FF_MANAGE_USERS_ROLES = os.getenv("FEATURE_FLAG_MANAGE_USERS_ROLES", False)
FEATURE_FLAG_REQ_ACCESS = os.getenv("FEATURE_FLAG_REQ_ACCESS", False)
