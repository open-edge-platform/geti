# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

include ../../../Makefile.shared-go

DOCKER_BUILD_CONTEXT := --build-context dev-go=docker-image://${BASE_IMAGES_REGISTRY}/dev-go:${BASE_DEV_GO_IMAGE_TAG} \
						--build-context debian_image=docker-image://${BASE_IMAGES_REGISTRY}/debian:${BASE_DEBIAN_IMAGE_TAG} \
						--build-context go_sdk=$(CWD)/interactive_ai/libs/go_sdk \
