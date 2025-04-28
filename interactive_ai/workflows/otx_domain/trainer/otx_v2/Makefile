include ../../../Makefile.shared-workflows

COMPONENT_NAME := otx2-training

DOCKER_BUILD_CONTEXT := --build-context libs=../../../../../libs

# TODO CVS-166188 remove the '-' and 'true' workaround after fixing the tests
test-unit: venv
	-uv run pytest --disable-warnings -v
	true

# TODO: Enable back venv when the tests are implemented
# test-component: venv
test-component:
	@echo "test-component not available"

# TODO: Enable back venv when the tests are implemented
# test-integration: venv
test-integration:
	@echo "test-integration not available"
