include ../../../Makefile.shared-python

COMPONENT_NAME := jobs

DOCKER_BUILD_CONTEXT := --build-context libs=../../../libs \
						--build-context iai_core=../../../interactive_ai/libs/iai_core_py \


# TODO CVS-165585 remove this target after fixing the stylechecks
static-code-analysis:
	-$(MAKE)  static-code-analysis-default
	true
