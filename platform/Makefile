# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

GO_SUBPROJECTS := $(shell find . -path "*/.venv" -prune -o -name "go.mod" -exec dirname {} \;)
PY_SUBPROJECTS := $(shell find . -path "*/.venv" -prune -o -name "pyproject.toml" -exec dirname {} \;)
SUBPROJECTS := $(GO_SUBPROJECTS) $(PY_SUBPROJECTS)

GO_SERVICES := $(shell find services -maxdepth 2 -path "*/.venv" -prune -o -name "go.mod" -exec dirname {} \;)
PY_SERVICES := $(shell find services -maxdepth 2 -path "*/.venv" -prune -o -name "pyproject.toml" -exec dirname {} \;)
SERVICES := $(GO_SERVICES) $(PY_SERVICES)

# Targets
.PHONY: clean clean-go clean-python build-image build-image-go build-image-python \
	push-image push-image-go push-image-python tests tests-go tests-python test-component \
	test-unit test-unit-go test-unit-python test-integration test-integration-go test-integration-python \
	static-code-analysis lint-go lint-python list-services list-subprojects 

clean: clean-go clean-python

clean-go:
	$(call run_for_each,$(GO_SUBPROJECTS),Cleaning for Go component,clean)

clean-python:	
	@$(call run_for_each,$(PY_SUBPROJECTS),Cleaning for Python component,clean)

build-image: build-image-go build-image-python

build-image-go:
	@$(call run_for_each,$(GO_SERVICES),Building image for Go component,build-image)

build-image-python:
	@$(call run_for_each,$(PY_SERVICES),Building image for Python component,build-image)

push-image: push-image-go push-image-python

push-image-go:
	@$(call run_for_each,$(GO_SERVICES),Pushing image for Go component,push-image)

push-image-python:
	@$(call run_for_each,$(PY_SERVICES),Pushing image for Python component,push-image)

tests: tests-go tests-python

tests-go:
	@$(call run_for_each,$(GO_SUBPROJECTS),Running tests for Go subproject,tests)

tests-python:
	@$(call run_for_each,$(PY_SUBPROJECTS),Running tests for Python subproject,tests)

test-unit: test-unit-go test-unit-python

test-unit-go:
	@$(call run_for_each,$(GO_SUBPROJECTS),Running unit tests for Go subproject,test-unit)

test-unit-python:
	@$(call run_for_each,$(PY_SUBPROJECTS),Running unit tests for Python subproject,test-unit)

test-integration: test-integration-go test-integration-python

test-integration-go:
	@$(call run_for_each,$(GO_SUBPROJECTS),Running integration tests for Go subproject,test-integration)

test-integration-python:
	@$(call run_for_each,$(PY_SUBPROJECTS),Running integration tests for Python subproject,test-integration)

test-component:
	@$(call run_for_each,$(PY_SUBPROJECTS),Running component tests for Python subproject,test-component)

static-code-analysis: lint-go lint-python

lint-go:
	@$(call run_for_each,$(GO_SUBPROJECTS),Performing static code analysis for Go subproject,static-code-analysis)

lint-python:
	@$(call run_for_each,$(PY_SUBPROJECTS),Performing static code analysis for Python subproject,static-code-analysis)

list-subprojects:
	@echo "Available subprojects:"
	@for svc in $(sort $(notdir $(SUBPROJECTS))); do \
		echo "  - $$svc"; \
	done

list-services:
	@echo "Available services:"
	@for svc in $(sort $(notdir $(SERVICES))); do \
		echo "  - $$svc"; \
	done

# Helper function to iterate over components
define run_for_each
    for item in $1; do \
        echo "$2 in $$item"; \
        (cd $$item && make $3); \
    done
endef
