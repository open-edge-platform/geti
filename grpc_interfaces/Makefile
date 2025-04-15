include ../Makefile.shared-python-uv

# Variables
PROTO_ROOT  	:= grpc_interfaces
PB_DIR          := pb
GO_OUT_BASE 	:= go/$(PB_DIR)
PY_OUT_BASE 	:= $(PB_DIR)
PROTOC      	:= protoc
YEAR 	        := $(shell date +%Y)
COPYRIGHT_OWNER := Intel Corporation

# Find all subdirectories containing .proto files
SERVICE_DIRS := $(shell find $(PROTO_ROOT) -name "*.proto" -exec dirname {} \; | sort | uniq)
# Get service names (e.g., account_service, credit_system)
SERVICES := $(shell find $(PROTO_ROOT) -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)

# Default target
.PHONY: all
all: generate

# Generate all code from proto files
.PHONY: generate
generate: generate-go generate-python

# Generate Go code for all services
.PHONY: generate-go
generate-go: $(foreach svc,$(SERVICES),generate-go-$(svc))

# Generate Python code for all services
.PHONY: generate-python
generate-python: $(foreach svc,$(SERVICES),generate-python-$(svc))

# Rule pattern for generating Go code for each service
.PHONY: generate-go-%
generate-go-%:
	@echo "Generating Go code for $* service..."
	@mkdir -p $(PROTO_ROOT)/$*/$(GO_OUT_BASE)
	@$(PROTOC) -I $(PROTO_ROOT)/$* \
		--proto_path=$(PROTO_ROOT)/$* \
		--go_out=paths=source_relative:$(PROTO_ROOT)/$*/$(GO_OUT_BASE) \
		--go-grpc_out=paths=source_relative:$(PROTO_ROOT)/$*/$(GO_OUT_BASE) \
		$(if $(filter $*,account_service), \
			--grpc-gateway_out=paths=source_relative:$(PROTO_ROOT)/$*/$(GO_OUT_BASE) \
			--openapiv2_out=$(PROTO_ROOT)/$*/$(GO_OUT_BASE),) \
		--experimental_allow_proto3_optional \
		$(PROTO_ROOT)/$*/*.proto
	@echo "Done generating Go code for $* service."
	@make add-license-go-$*


# Rule pattern for generating Python code for each service
.PHONY: generate-python-%
generate-python-%:
	@echo "Generating Python code for $* service..."
	@mkdir -p $(PROTO_ROOT)/$*/$(PY_OUT_BASE)
	@cd $(PROTO_ROOT)/$* && python -m grpc_tools.protoc --plugin=protoc_gen_mypy -I. \
		--proto_path=. \
		--python_out=$(PY_OUT_BASE) \
		--grpc_python_out=$(PY_OUT_BASE) \
		--mypy_out=$(PY_OUT_BASE) \
		*.proto
	@echo "Fixing imports for relative imports..."
	@find $(PROTO_ROOT)/$*/$(PY_OUT_BASE) -name "*.py" -exec sed -i 's/^import \(.*_pb2\)/from . import \1/' {} \;
	@echo "Done generating Python code for $* service."
	@make add-license-python-$*

# Generate code for specific service (both Go and Python)
.PHONY: generate-service-%
generate-service-%: generate-go-% generate-python-%
	@echo "Generated code for $* service (Go and Python)."

# List all services
.PHONY: list-services
list-services:
	@echo "Available services:"
	@for svc in $(SERVICES); do \
		echo "  - $$svc"; \
	done

# Clean generated files
.PHONY: clean
clean: clean-go clean-python

# Clean Go generated files
.PHONY: clean-go
clean-go: $(foreach svc,$(SERVICES),clean-go-$(svc))

# Clean Python generated files
.PHONY: clean-python
clean-python: $(foreach svc,$(SERVICES),clean-python-$(svc))

# Clean specific service
.PHONY: clean-service-%
clean-service-%:
	@echo "Cleaning generated files for $* service..."
	@rm -rf $(PROTO_ROOT)/$*/$(GO_OUT_BASE)
	@rm -rf $(PROTO_ROOT)/$*/$(PY_OUT_BASE)
	@echo "Done cleaning $* service files."

# Install required protoc plugins
.PHONY: install-deps
install-deps: install-go-deps install-python-deps

# Install Go protoc plugins
.PHONY: install-go-deps
install-go-deps:
	@echo "Installing Go protoc plugins..."
	@go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
	@go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
	@go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@latest
	@go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-openapiv2@latest

	@echo "Done installing Go plugins."

# Install Python protoc plugins
.PHONY: install-python-deps
install-python-deps: venv
	@echo "Installing Python protoc plugins..."
	@uv pip install .
	@echo "Done installing Python plugins."

# Verify protoc and plugins are installed
.PHONY: verify-tools
verify-tools:
	@which $(PROTOC) > /dev/null || (echo "Error: protoc not found. Please install protobuf compiler." && exit 1)
	@echo "Checking Go tools..."
	@which protoc-gen-go > /dev/null || (echo "Warning: protoc-gen-go not found. Run 'make install-go-deps' to install.")
	@which protoc-gen-go-grpc > /dev/null || (echo "Warning: protoc-gen-go-grpc not found. Run 'make install-go-deps' to install.")
	@echo "Checking Python tools..."
	@pip show grpcio-tools > /dev/null 2>&1 || (echo "Warning: grpcio-tools not found. Run 'make install-python-deps' to install.")
	@echo "Tools verification complete."

# Format proto files
.PHONY: format
format:
	@echo "Formatting proto files..."
	@which clang-format > /dev/null || (echo "Error: clang-format not found. Please install it." && exit 1)
	@find $(PROTO_ROOT) -name "*.proto" -exec clang-format -i {} \;
	@echo "Done formatting."

# Add license header to Python files for specific service
.PHONY: add-license-python
add-license-python-%:
	@echo "Adding license header to Python files..."
	@for file in $$(find $(PROTO_ROOT)/$* -name "*.py"); do \
		if ! grep -q "LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE" $$file; then \
			tmpfile=$$(mktemp); \
			echo "# Copyright (C) $(YEAR) $(COPYRIGHT_OWNER)" >> $$tmpfile; \
			echo "# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE" >> $$tmpfile; \
			echo "" >> $$tmpfile; \
			cat $$file >> $$tmpfile; \
			mv $$tmpfile $$file; \
			echo "Done adding license header to $$file"; \
		fi; \
	done

# Add license header to Go files for specific service
.PHONY: add-license-go
add-license-go-%:
	@echo "Adding license header to Go files..."
	@for file in $$(find $(PROTO_ROOT)/$*/go -name "*.go"); do \
		if ! grep -q "LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE" $$file; then \
			tmpfile=$$(mktemp); \
			echo "// Copyright (C) $(YEAR) $(COPYRIGHT_OWNER)" >> $$tmpfile; \
			echo "// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE" >> $$tmpfile; \
			echo "" >> $$tmpfile; \
			cat $$file >> $$tmpfile; \
			mv $$tmpfile $$file; \
			echo "Done adding license header to $$file"; \
		fi; \
	done

mypy: venv
	uv run mypy ./grpc_interfaces ./tests --config-file=pyproject.toml

build-image:
	@echo "No build-image target defined. Skipping..."

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all (default)             - Generate all code from proto files"
	@echo "  generate                  - Generate all code from proto files"
	@echo "  generate-go               - Generate all Go code"
	@echo "  generate-python           - Generate all Python code"
	@echo "  generate-go-NAME          - Generate Go code for specific service (replace NAME with service name)"
	@echo "  generate-python-NAME      - Generate Python code for specific service (replace NAME with service name)"
	@echo "  generate-service-NAME     - Generate code for specific service (replace NAME with service name)"
	@echo "  list-services             - List all available services"
	@echo "  clean                     - Remove all generated files"
	@echo "  clean-go                  - Remove only Go generated files"
	@echo "  clean-python              - Remove only Python generated files"
	@echo "  clean-service-NAME        - Clean generated files for specific service"
	@echo "  install-deps              - Install all required protoc plugins"
	@echo "  install-go-deps           - Install only Go protoc plugins"
	@echo "  install-python-deps       - Install only Python protoc plugins"
	@echo "  verify-tools              - Verify that all required tools are installed"
	@echo "  format                    - Format proto files using clang-format"
	@echo "  add-license-python-NAME   - Add license header to Python files for specific service"
	@echo "  add-license-go-NAME       - Add license header to Go files for specific service"
	@echo "  help                      - Show this help message"
	@echo ""
	@echo "For service-specific commands, replace NAME with one of the following:"
	@for svc in $(SERVICES); do \
		echo "  - $$svc"; \
	done
