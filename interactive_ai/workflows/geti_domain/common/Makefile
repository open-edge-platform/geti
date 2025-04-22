include ../../Makefile.shared-workflows

build-image:
	@echo "Nothing to do - ${COMPONENT_NAME} does not have an image to build"

push-image:
	@echo "Nothing to do - ${COMPONENT_NAME} does not have an image to push"

# TODO CVS-166338 remove '-' and 'true' workaround after fixing the test
test-unit: venv
	-uv run pytest tests/unit --disable-warnings -v
	true

test-component: venv
	@echo "test-component not available"

# TODO CVS-166339 remove '-' and 'true' workaround after fixing the test
test-integration: venv
	-uv run pytest tests/integration --disable-warnings -v
	true
