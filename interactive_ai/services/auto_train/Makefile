include ../../../Makefile.shared-python-uv

DOCKER_BUILD_CONTEXT := --build-context libs=../../../libs \
						--build-context sc_sdk=../../../interactive_ai/libs/sc_sdk \
						--build-context grpc_interfaces=../../../grpc_interfaces \
						--build-context training_extensions_v2=docker-image://$(BASE_IMAGES_REGISTRY)/training-extensions-v2:$(BASE_OTE_V2_IMAGE_TAG) \
