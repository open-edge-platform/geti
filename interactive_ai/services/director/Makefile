include ../../../Makefile.shared-python-uv

DOCKER_BUILD_CONTEXT := --build-context schemas=../api \
						--build-context libs=../../../libs \
						--build-context sc_sdk=../../../interactive_ai/libs/sc_sdk \
						--build-context grpc_interfaces=../../../grpc_interfaces \
						--build-context training_extensions_v2=docker-image://$(BASE_IMAGES_REGISTRY)/training-extensions-v2:$(BASE_OTE_V2_IMAGE_TAG) \

# TODO CVS-165943 remove this target after fixing the tests
# NOTE: the tests are fully disabled here because they timeout in the CI after getting stuck
test-unit:
	echo "test-unit is disabled"
	true

# TODO CVS-165944 remove this target after fixing the tests
# NOTE: the tests are fully disabled here because they timeout in the CI after repeatedly failing to connect to Kafka
test-integration:
	echo "test-integration is disabled"
	true
