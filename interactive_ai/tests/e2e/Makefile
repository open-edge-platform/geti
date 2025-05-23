include ../../../Makefile.shared-python

MAKEFILE_DIR := $(shell pwd)
OPENAPI_YAML_SPEC := ../../../docs/rest_api/openapi_internal.yaml
OPENAPI_JSON_SPEC := /tmp/openapi_internal.json
CLIENT_NAME := geti_client
SPEC_HASH_FILE := .openapi_spec_hash

.PHONY: all check_yaml_spec generate_json_spec generate_client generate_client_if_needed test test_wip test_smoke

all: tests

venv:
	$(MAKE) generate_client_if_needed;
	uv sync

check_yaml_spec:
	@if [ ! -f $(OPENAPI_YAML_SPEC) ]; then \
		echo "Error: OpenAPI YAML spec file not found at $(OPENAPI_YAML_SPEC)"; \
		exit 1; \
	fi

generate_json_spec: check_yaml_spec
	@command -v swagger-cli >/dev/null 2>&1 || { echo >&2 "swagger-cli is not installed. Aborting."; exit 1; }
	swagger-cli bundle $(OPENAPI_YAML_SPEC) -o $(OPENAPI_JSON_SPEC) --dereference

generate_client: generate_json_spec
	@command -v openapi-generator-cli >/dev/null 2>&1 || { echo >&2 "openapi-generator-cli is not installed. Aborting."; exit 1; }
	openapi-generator-cli generate -i $(OPENAPI_JSON_SPEC) -g python -o $(CLIENT_NAME) --package-name $(CLIENT_NAME)

generate_client_if_needed: generate_json_spec
	@SHA=$$(sha256sum $(OPENAPI_JSON_SPEC) | cut -d ' ' -f 1); \
	if [ -d $(CLIENT_NAME) ] && [ -f $(SPEC_HASH_FILE) ] && [ "$$(cat $(SPEC_HASH_FILE))" = "$$SHA" ]; then \
		echo "geti_client is already up to date"; \
	else \
		echo "OpenAPI spec has changed, regenerating geti_client"; \
		$(MAKE) generate_client; \
	fi; \
	echo $$SHA > $(SPEC_HASH_FILE)

tests: venv
	@if [ -z "$(FEATURE)" ]; then \
	  echo "Selected features: all"; \
	  TARGET="features"; \
	else \
	  echo "Selected feature: $(FEATURE)"; \
	  TARGET="features/$(FEATURE).feature"; \
	fi; \
	if [ -z "$(BDD_TAG)" ] || [ "$(BDD_TAG)" = "all" ]; then \
		TAG_OPTION=""; \
	else \
		echo "Selected tags: $(BDD_TAG)"; \
		TAG_OPTION='--tags=$(BDD_TAG)'; \
	fi; \
	uv run -m behave $$TAG_OPTION $$TARGET --junit --junit-directory $(MAKEFILE_DIR)/reports/junit

test_wip: venv
	@echo "Running WIP tests..."
	uv run behave --wip features

test_smoke: venv
	@$(MAKE) tests BDD_TAG=@smoke

report: venv
	@echo "Generating HTML report..."
	@mkdir -p $(MAKEFILE_DIR)/reports/html
	@. $(ACTIVATE); for file in reports/junit/*.xml; do \
	  basefile=$$(basename "$$file" .xml); \
	  junit2html "$$file" "reports/html/$$basefile.html"; \
	done

mypy: venv
	uv run mypy features --config-file=pyproject.toml

build-image:
	@echo "Skipping build image stage for e2e tests"