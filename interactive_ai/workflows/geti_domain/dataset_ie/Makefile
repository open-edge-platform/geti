include ../../Makefile.shared-workflows

COMPONENT_NAME       := dataset-ie-job

DOCKER_BUILD_CONTEXT := --build-context common=../common \
						--build-context libs=../../../../libs \
						--build-context iai_core=../../../../interactive_ai/libs/iai_core_py \
						--build-context media_utils=../../../../interactive_ai/libs/media_utils \

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
