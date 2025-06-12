include ../../../../Makefile.shared-workflows

.PHONY: build-image

COMPONENT_NAME      := otx2-training

DOCKER_BUILD_CONTEXT := --build-context libs=../../../../../../libs

build-image: install_common_libs
	@echo "Building docker image for component: ${COMPONENT_NAME}"
	@docker build \
		${DOCKER_EXTRA_ARGS} \
		${DOCKER_BUILD_CONTEXT} \
		--label "org.opencontainers.image.description=GPU trainer for Geti" \
		-t ${IMAGES_REGISTRY}/${COMPONENT_NAME}:${TAG} \
		-f ./Dockerfile ..

ruff: venv
	uv run ruff check .. --config pyproject.toml
	uv run ruff format --check .. --config pyproject.toml

mypy: venv
	uv run mypy .. --config-file=pyproject.toml

style-fix: venv
	uv run ruff check .. --config pyproject.toml --fix
	uv run ruff format .. --config pyproject.toml

# TODO CVS-166188 remove the '-' and 'true' workaround after fixing the tests
test-unit: venv
	-PYTHONPATH=../scripts uv run pytest ../tests --disable-warnings -v
	true

test-component: venv
	@echo "test-component not available"

test-integration: venv
	@echo "test-integration not available"
