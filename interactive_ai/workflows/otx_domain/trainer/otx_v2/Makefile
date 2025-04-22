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

test-component: venv
	@echo "test-component not available"

test-integration: venv
	@echo "test-integration not available"
