# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

include ../../../Makefile.shared-python

COMPONENT_NAME = install-upgrade

ORAS := /usr/local/bin/oras
ORAS_VERSION := 1.2.3
ORAS_DIR := oras-install

ifneq (,$(wildcard $(ORAS)))
    ORAS_BINARY := $(ORAS)
else
    ORAS_BINARY := ./$(ORAS_DIR)/oras
endif

get_oras: $(ORAS)
$(ORAS):
	curl -LO "https://github.com/oras-project/oras/releases/download/v$(ORAS_VERSION)/oras_$(ORAS_VERSION)_linux_amd64.tar.gz"
	mkdir -p $(ORAS_DIR)/
	tar -zxf oras_$(ORAS_VERSION)_*.tar.gz -C $(ORAS_DIR)/
	rm -rf oras_$(ORAS_VERSION)_*.tar.gz

remove_oras:
	rm -rf $(ORAS_DIR)

oras_push: prepare_manifest
	$(ORAS_BINARY) push $(DEV_REGISTRY)/geti/geti-manifest:$(PRODUCT_BUILD) \
		--artifact-type=application/text \
		geti-manifest.yaml

prepare_manifest:
	VERSION=$(PRODUCT_BUILD) \
	REGISTRY=$(DEV_REGISTRY) \
	envsubst < geti-manifest.yaml.template > geti-manifest.yaml
