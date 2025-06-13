# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
include ../../../Makefile.shared-python

.PHONY: build_installer_dev

COMPONENT_NAME = installer

DOCKER_BUILD_CONTEXT := --build-context libs=../../../libs \
 						--build-context geti_controller_chart=../geti_controller/.build

build_installer_dev: build-image
	$(eval CONTAINER_ID := $(shell docker run -d --rm dev-registry.toolbox.iotg.sclab.intel.com/open-edge-platform/geti/${COMPONENT_NAME}:${TAG} sleep 10))
	@sleep 2
	docker cp $(CONTAINER_ID):/app/dist/platform_installer .