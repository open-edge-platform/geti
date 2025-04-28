include ../../../Makefile.shared-workflows

# TODO CVS-166109 remove this target after adding the Dockerfile
build-image:
	@echo "Dockerfile not available yet for ${COMPONENT_NAME}"

# TODO CVS-166109 remove this target after adding the Dockerfile
push-image:
	@echo "Dockerfile not available yet for ${COMPONENT_NAME}"

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
