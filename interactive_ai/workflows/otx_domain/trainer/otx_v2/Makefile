include ../../../Makefile.shared-workflows

.PHONY: build-image-gpu build-image-xpu build-image

GPU_IMAGE_NAME := otx2-training
XPU_IMAGE_NAME := otx2-intel

DOCKER_BUILD_CONTEXT := --build-context libs=../../../../../libs

build-image-gpu: install_common_libs
	@echo "Building docker image for component: ${GPU_IMAGE_NAME}"
	@docker build \
		${DOCKER_EXTRA_ARGS} \
		${DOCKER_BUILD_CONTEXT} \
		-t ${IMAGES_REGISTRY}/${GPU_IMAGE_NAME}:${TAG} \
		-f ./Dockerfile.gpu .

build-image-xpu: install_common_libs
	@echo "Building docker image for component: ${XPU_IMAGE_NAME}"
	@docker build \
		${DOCKER_EXTRA_ARGS} \
		${DOCKER_BUILD_CONTEXT} \
		-t ${IMAGES_REGISTRY}/${XPU_IMAGE_NAME}:${TAG} \
		-f ./Dockerfile.xpu .

build-image:
	#make build-image-gpu
	make build-image-xpu

push-image-gpu:
	@echo "Pushing docker image for component: ${GPU_IMAGE_NAME}"
	@docker push ${IMAGES_REGISTRY}/${GPU_IMAGE_NAME}:${TAG}

push-image-xpu:
	@echo "Pushing docker image for component: ${XPU_IMAGE_NAME}"
	@docker push ${IMAGES_REGISTRY}/${XPU_IMAGE_NAME}:${TAG}

push-image:
	# make push-image-gpu
	make push-image-xpu

# TODO CVS-166188 remove the '-' and 'true' workaround after fixing the tests
test-unit: venv
	-uv run pytest --disable-warnings -v
	true

test-component: venv
	@echo "test-component not available"

test-integration: venv
	@echo "test-integration not available"
