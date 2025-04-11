include ../../Makefile.shared-python

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

run: venv
	. $(ACTIVATE); PYTHONPATH=. py.test tests

run_ff: venv
	. $(ACTIVATE); FEATURE_FLAG_MANAGE_USERS=true \
	FEATURE_FLAG_MANAGE_USERS_ROLES=true \
	FEATURE_FLAG_ACC_SVC_MOD=true \
	FEATURE_FLAG_REQ_ACCESS=true \
	PYTHONPATH=. py.test tests

install_common_libs:
	@rm -rf common_libs
	@mkdir common_libs
	@cp -r ../../libs/telemetry_tools  common_libs/
	@cp -r ../../grpc_interfaces  common_libs/
	@. $(ACTIVATE); pip install ${PIP_INSTALL_PARAMS} common_libs/telemetry_tools
	@. $(ACTIVATE); pip install ${PIP_INSTALL_PARAMS} common_libs/grpc_interfaces[account_service,credit_system]
