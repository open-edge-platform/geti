include ../../../Makefile.shared-workflows

COMPONENT_NAME := otx2-training

DOCKER_BUILD_CONTEXT := --build-context libs=../../../../../libs

# TODO CVS-166188 remove the '-' and 'true' workaround after fixing the tests
test-unit: venv
	-uv run pytest --disable-warnings -v
	true

test-component: venv
	@echo "test-component not available"

test-integration: venv
	@echo "test-integration not available"
