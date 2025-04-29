include ../../../../Makefile.shared-python

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

run: venv
	@PYTHONPATH=. uv run pytest tests

run_ff: venv
	FEATURE_FLAG_MANAGE_USERS=true \
	FEATURE_FLAG_MANAGE_USERS_ROLES=true \
	FEATURE_FLAG_ACC_SVC_MOD=true \
	FEATURE_FLAG_REQ_ACCESS=true \
	PYTHONPATH=. uv run pytest tests
