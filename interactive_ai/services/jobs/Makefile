include ../../../Makefile.shared-python

DOCKER_BUILD_CONTEXT := --build-context libs=../../../libs \
						--build-context iai_core_py=../../../interactive_ai/libs/iai_core_py \
						--build-context grpc_interfaces=../../../grpc_interfaces \

# TODO CVS-165585 remove this target after fixing the stylechecks
static-code-analysis:
	-$(MAKE)  static-code-analysis-default
	true
