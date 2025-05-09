include ../../Makefile.shared-workflows

build-image:
	@echo "Nothing to do - ${COMPONENT_NAME} does not have an image to build"

publish-image:
	@echo "Nothing to do - ${COMPONENT_NAME} does not have an image to push"

test-component: venv
	@echo "test-component not available"

venv: pre-venv
	uv lock --check
	# Cuda bindings is a sub-dependency of datumaro and is not needed for Geti.
	# The install is therefore skipped here for compatibility with systems that don't support cuda
	uv sync --frozen ${PIP_INSTALL_PARAMS} --no-install-package cuda-bindings
