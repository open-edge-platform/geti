# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
include ../Makefile.build

# Variables
# SERVICES      -> server-like components that can be built and deployed independently
# WORKFLOWS 	-> long-running jobs to execute a specific task
# SUBPROJECTS   -> union of libs, services and workflows

GO_SERVICES := $(call find_subprojects,services,go.mod,2)
PY_SERVICES := $(call find_subprojects,services,pyproject.toml,2)
SERVICES := $(GO_SERVICES) $(PY_SERVICES)

GO_SUBPROJECTS := $(call find_subprojects,.,go.mod)
PY_SUBPROJECTS := $(call find_subprojects,.,pyproject.toml)
SUBPROJECTS := $(GO_SUBPROJECTS) $(PY_SUBPROJECTS)

WORKFLOWS := $(call find_subprojects,workflows,job,3)

GO_BUILDABLE_SUBPROJECTS := $(GO_SERVICES)  # assumption: no workflows in Go
PY_BUILDABLE_SUBPROJECTS := $(PY_SERVICES) $(WORKFLOWS)
BUILDABLE_SUBPROJECTS := $(GO_BUILDABLE_SUBPROJECTS) $(PY_BUILDABLE_SUBPROJECTS)

# Targets
.PHONY: list-workflows
list-workflows:
	@echo "Available workflows:"
	@for svc in $(notdir $(WORKFLOWS)); do \
		echo "  - $$svc"; \
	done

