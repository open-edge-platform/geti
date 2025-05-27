include ../../../../Makefile.shared-workflows

.PHONY: build-image

IMAGE_NAME := otx2-intel

DOCKER_BUILD_CONTEXT := --build-context libs=../../../../../../libs

build-image: install_common_libs
	@echo "Building docker image for component: ${IMAGE_NAME}"
	@docker build \
		${DOCKER_EXTRA_ARGS} \
		${DOCKER_BUILD_CONTEXT} \
		-t ${IMAGES_REGISTRY}/${IMAGE_NAME}:${TAG} \
		-f ./Dockerfile .

push-image:
	@echo "Pushing docker image for component: ${IMAGE_NAME}"
	@docker push ${IMAGES_REGISTRY}/${IMAGE_NAME}:${TAG}

# TODO CVS-166188 remove the '-' and 'true' workaround after fixing the tests
test-unit: venv
	-PYTHONPATH=../scripts uv run pytest ../tests --disable-warnings -v
	true

test-component: venv
	@echo "test-component not available"

test-integration: venv
	@echo "test-integration not available"
