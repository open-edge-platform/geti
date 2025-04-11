# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

include ../../../Makefile.shared-go

DOCKER_BUILD_CONTEXT := --build-context dev-go=docker-image://${BASE_IMAGES_REGISTRY}/dev-go:${BASE_DEV_GO_IMAGE_TAG} \
						--build-context debian_image=docker-image://${BASE_IMAGES_REGISTRY}/debian:${BASE_DEBIAN_IMAGE_TAG} \
						--build-context account_service_client=$(CWD)/grpc_interfaces/grpc_interfaces/account_service/go \

