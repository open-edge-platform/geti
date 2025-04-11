# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

include ../../../Makefile.shared-go

DOCKER_BUILD_CONTEXT := --build-context dev-go=docker-image://${BASE_IMAGES_REGISTRY}/dev-go:${BASE_DEV_GO_IMAGE_TAG} \
						--build-context debian_image=docker-image://${BASE_IMAGES_REGISTRY}/debian:${BASE_DEBIAN_IMAGE_TAG} \
						--build-context credit_system=$(CWD)/grpc_interfaces/grpc_interfaces/credit_system/go \
						--build-context account_service_grpc=$(CWD)/grpc_interfaces/grpc_interfaces/account_service/go \

destroy_deploy:
	IMAGE_TAG=${IMAGES_REGISTRY}/account-service:${TAG} docker compose down -v
	docker image rm ${IMAGES_REGISTRY}/account-service:${TAG}

deploy_local: build-image
	FEATURE_FLAG_MANAGE_USERS=true \
	FEATURE_FLAG_MANAGE_USERS_ROLES=true \
	FEATURE_FLAG_ACC_SVC_MOD=true \
	FEATURE_FLAG_REQ_ACCESS=true \
	DB_USER=user_$$(date +%s) \
	DB_PASSWORD=password_$$(date +%s | sha256sum | base64 | head -c 32 ; echo) \
	DB_NAME=db_$$(date +%s) \
	IMAGE_TAG=${IMAGES_REGISTRY}/account-service:${TAG} docker compose -f docker-compose.yml up --build -d
