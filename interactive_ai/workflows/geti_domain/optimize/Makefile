include ../../Makefile.shared-workflows

COMPONENT_NAME       := optimize-job

DOCKER_BUILD_CONTEXT := --build-context common=../common \
						--build-context libs=../../../../libs \
						--build-context sc_sdk=../../../../interactive_ai/libs/sc_sdk \
						--build-context media_utils=../../../../interactive_ai/libs/media_utils \
						--build-context grpc_interfaces=../../../../grpc_interfaces \

test-unit: venv-dev
	uv run pytest tests/unit --disable-warnings -v

test-component: venv-dev
	@echo "test-component not available"

test-integration: venv-dev
	@echo "test-integration not available"
