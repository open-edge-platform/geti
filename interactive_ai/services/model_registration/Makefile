include ../../../Makefile.shared-python-uv

DOCKER_BUILD_CONTEXT := --build-context grpc_interfaces=../../../grpc_interfaces \

# TODO CVS-165596 remove this target after fixing the stylechecks
static-code-analysis:
	-$(MAKE)  static-code-analysis-default
	true

