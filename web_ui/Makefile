# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

builder:
	@echo "Not applicable"
