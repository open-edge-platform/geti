include ../../../Makefile.common

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

IMAGE ?= dex-templates-init-copy
IMAGE_TAG ?= $(UPSTREAM)/$(IMAGE):$(TAG)
REGISTRY_IMAGE_TAG ?= $(REGISTRY_TAG)/$(IMAGE):$(TAG)

.PHONY: build

remove_image:
	@echo "Remove image from docker daemon"
	docker image rm $(UPSTREAM)/$(IMAGE):$(TAG)

build:

	$(eval IMAGE = $(IMAGE))

	$(DOCKER_COMMAND) \
		$(BUILDKIT_CACHE_PARAMS) \
		$(DOCKER_EXTRA_FLAGS) \
		$(PROXY) \
		--build-context debian_image=docker-image://$(DEBIAN_IMAGE) \
		-t $(IMAGE_TAG) \
		-f Dockerfile .

build_local: _check_buildkit_builder_exists
	@echo "Processing base docker images for $(IMAGE)..."
	@make build || true
	@cd $(CWD) && make remove_buildkit_builder && cd -

build_and_push:
	$(MAKE) build
	$(MAKE) push

push:
	docker pull $(IMAGE_TAG)
	docker tag $(IMAGE_TAG) $(REGISTRY_IMAGE_TAG)
	docker push $(REGISTRY_IMAGE_TAG)

save:
	@echo "Storing image in the archive file"
	docker save $(UPSTREAM)/$(IMAGE):$(TAG) | pigz > $(DEPS_IMAGES_DIR)/$(IMAGE)_$(TAG).tar.gz && test $${PIPESTATUS[0]} -eq 0

### ---------------------
### Component replacement
### ---------------------
current_tag:
	$(eval REPLACEMENT_TAG=$(shell sh -c "kubectl get deployment -n $(PLATFORM_NAMESPACE) impt-dex \
	-o jsonpath='{.spec.template.spec.initContainers[].image}'"))

rebuild_images: current_tag
	@make build_local

replace_images:
	$(eval ENVIRONMENT=$(shell sh -c "kubectl get nodes -o jsonpath='{.items[:].status.addresses[0].address}'"))
	@ssh $(PATCH_IMAGES_ENV_USER)@$(ENVIRONMENT) sudo ctr image pull $(IMAGE_TAG)
	@ssh $(PATCH_IMAGES_ENV_USER)@$(ENVIRONMENT) sudo ctr images tag --force $(IMAGE_TAG) $(REPLACEMENT_TAG)
	@kubectl get pods -n $(PLATFORM_NAMESPACE) --no-headers=true | awk '/impt-dex/{print $$1}' | xargs kubectl delete pod -n $(PLATFORM_NAMESPACE)

replace_component: rebuild_images replace_images
