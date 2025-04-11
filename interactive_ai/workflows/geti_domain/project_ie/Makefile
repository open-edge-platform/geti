include ../../../../Makefile.shared-python-uv

COMPONENT_NAME       := project-ie-job

DOCKER_BUILD_CONTEXT := --build-context common=../common \
						--build-context libs=../../../../libs \
						--build-context sc_sdk=../../../../interactive_ai/libs/sc_sdk \
						--build-context media_utils=../../../../interactive_ai/libs/media_utils \
						--build-context data_migration=../../../../interactive_ai/data_migration \
						--build-context grpc_interfaces=../../../../grpc_interfaces \

test-unit: venv-dev
	uv run pytest tests/unit --disable-warnings -v

test-component: venv-dev
	@echo "test-component not available"

test-integration: venv-dev
	uv run pytest tests/integration --disable-warnings -v
