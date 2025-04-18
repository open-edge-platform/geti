# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

include ../Makefile.shared-builders

.PHONY: build-image

build-image:
	@echo "Building docker image for: ${BUILDER_IMAGE_NAME}"
	@echo ${BUILDER_DOCKER_EXTRA_ARGS}
	@docker build \
		${BUILDER_DOCKER_EXTRA_ARGS} \
		-t ${BUILDER_IMAGE_NAME}:${BUILDER_TAG} \
		-f ./Dockerfile .
