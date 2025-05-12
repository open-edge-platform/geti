include ../../Makefile.shared-workflows

COMPONENT_NAME       := optimize-job

DOCKER_BUILD_CONTEXT := --build-context common=../common \
						--build-context libs=../../../../libs \
						--build-context iai_core=../../../../interactive_ai/libs/iai_core_py \
						--build-context media_utils=../../../../interactive_ai/libs/media_utils \
						--build-context grpc_interfaces=../../../../grpc_interfaces \

test-unit: venv
	uv run pytest tests/unit --disable-warnings -v

test-component: venv
	@echo "test-component not available"

test-integration: venv
	@echo "test-integration not available"

venv: pre-venv
	uv lock --check
	# Cuda bindings is a sub-dependency of datumaro and is not needed for Geti.
	# The install is therefore skipped here for compatibility with systems that don't support cuda
	uv sync --frozen ${PIP_INSTALL_PARAMS} --no-install-package cuda-bindings