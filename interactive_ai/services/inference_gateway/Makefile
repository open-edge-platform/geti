include ../../../Makefile.shared-go

DOCKER_BUILD_CONTEXT := --build-context dev-go=docker-image://${BASE_IMAGES_REGISTRY}/dev-go:${BASE_DEV_GO_IMAGE_TAG} \
						--build-context debian_image=docker-image://${BASE_IMAGES_REGISTRY}/debian:${BASE_DEBIAN_IMAGE_TAG} \
						--build-context go_sdk=$(CWD)/interactive_ai/libs/go_sdk \
						--build-context modelmesh=$(CWD)/grpc_interfaces/grpc_interfaces/model_mesh/go/pb \
						--build-context modelregistration=$(CWD)/grpc_interfaces/grpc_interfaces/model_registration/go/pb \
						--build-context predict=$(CWD)/grpc_interfaces/grpc_interfaces/predict/go/pb \
						--build-arg BASE_FFMPEG_TAG=$(BASE_FFMPEG_TAG) \
