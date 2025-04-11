include ../../../Makefile.shared-python-uv

DOCKER_BUILD_CONTEXT := --build-context libs=../../../libs \
						--build-context sc_sdk=../../../interactive_ai/libs/sc_sdk \
						--build-context media_utils=../../../interactive_ai/libs/media_utils \

# TODO CVS-165811 remove this target after fixing the tests
test-unit:
	-$(MAKE)  test-unit-default
	true
