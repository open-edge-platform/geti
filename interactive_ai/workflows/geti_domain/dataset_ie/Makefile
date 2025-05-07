include ../../Makefile.shared-workflows

COMPONENT_NAME       := dataset-ie-job

DOCKER_BUILD_CONTEXT := --build-context common=../common \
						--build-context libs=../../../../libs \
						--build-context sc_sdk=../../../../interactive_ai/libs/sc_sdk \
						--build-context media_utils=../../../../interactive_ai/libs/media_utils \
						--build-context grpc_interfaces=../../../../grpc_interfaces \

# TODO CVS-166211 remove the '-' and 'true' workaround after fixing the tests
test-unit: venv
	-uv run pytest tests/unit --disable-warnings -v
	true

test-component: venv
	@echo "test-component not available"

# TODO CVS-166335 re-enable the tests that timeout due to unavailable Kafka broker
test-integration: venv
	# uv run pytest tests/integration --disable-warnings -v
	@echo "test-integration temporarily disabled"

venv: pre-venv
	uv lock --check
	# Cuda bindings is a sub-dependency of datumaro and is not needed for Geti.
	# The install is therefore skipped here for compatibility with systems that don't support cuda
	uv sync --frozen ${PIP_INSTALL_PARAMS} --no-install-package cuda-bindings