# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
include ../Makefile.build

GO_SERVICES := $(call find_subprojects,services,go.mod,2)
PY_SERVICES := $(call find_subprojects,services,pyproject.toml,2)
SERVICES := $(GO_SERVICES) $(PY_SERVICES)

GO_SUBPROJECTS := $(call find_subprojects,.,go.mod)
PY_SUBPROJECTS := $(call find_subprojects,.,pyproject.toml)
SUBPROJECTS := $(GO_SUBPROJECTS) $(PY_SUBPROJECTS)

GO_BUILDABLE_SUBPROJECTS := $(GO_SERVICES)
PY_BUILDABLE_SUBPROJECTS := $(PY_SERVICES)
BUILDABLE_SUBPROJECTS := $(GO_BUILDABLE_SUBPROJECTS) $(PY_BUILDABLE_SUBPROJECTS)
