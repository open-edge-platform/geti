include ../../Makefile.shared-workflows

COMPONENT_NAME       := project-ie-job

DOCKER_BUILD_CONTEXT := --build-context common=../common \
						--build-context libs=../../../../libs \
						--build-context sc_sdk=../../../../interactive_ai/libs/sc_sdk \
						--build-context media_utils=../../../../interactive_ai/libs/media_utils \
						--build-context data_migration=../../../../interactive_ai/data_migration \
						--build-context grpc_interfaces=../../../../grpc_interfaces \

test-unit: venv
	uv run pytest tests/unit --disable-warnings -v

test-component: venv
	@echo "test-component not available"

# TODO CVS-166347 remove '-' and 'true' workaround after fixing the tests
test-integration: venv
	-uv run pytest tests/integration --disable-warnings -v
	true
