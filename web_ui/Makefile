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

include ../Makefile.shared

# build contexts for web-ui image
DOCKER_BUILD_CONTEXT := --build-context nginx_image=docker-image://public.ecr.aws/nginx/nginx:1.27-bookworm \
						--build-context node_image=docker-image://public.ecr.aws/docker/library/node:22.12-bookworm-slim \
						--build-context docs_context=../docs \
						--build-context api_context=../interactive_ai/services/api

tests: test-unit test-component test-integration

# At the moment we do not support testing and static code analysis via Makefile
# please use npm direclty instead
test-unit:
	@echo "Not applicable"

test-component:
	@echo "Not applicable"

test-integration:
	@echo "Not applicable"

static-code-analysis:
	@echo "Not applicable"
