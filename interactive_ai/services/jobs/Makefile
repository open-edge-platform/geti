include ../../../Makefile.shared-python

DOCKER_BUILD_CONTEXT := --build-context libs=../../../libs \
						--build-context sc_sdk=../../../interactive_ai/libs/sc_sdk \
						--build-context grpc_interfaces=../../../grpc_interfaces \

# TODO CVS-165585 remove this target after fixing the stylechecks
static-code-analysis:
	-$(MAKE)  static-code-analysis-default
	true
