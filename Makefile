# Copyright (C) 2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

.PHONY: build clean push static-code-analysis tests test-unit test-integration test-component

PROJECTS = interactive_ai platform web_ui
CHART_TEMPLATES_LIST = $(shell find . -name "Chart.yaml.template" | while read -r filepath; do dirname $$(dirname $$filepath); done)
.DEFAULT_GOAL := build

build:
	echo "Building images for all projects..."
	@for dir in $(PROJECTS); do \
		echo "Running make build-image in $$dir..."; \
		$(MAKE) -C $$dir build-image; \
	done

build-chart:
	echo "Building charts for all projects..."
	@for dir in $(CHART_TEMPLATES_LIST); do \
		echo "Running make build-chart in $$dir..."; \
		$(MAKE) -C $$dir build-chart; \
	done

clean-chart:
	echo "Clean charts for all projects..."
	@for dir in $(CHART_TEMPLATES_LIST); do \
		echo "Running make build-chart in $$dir..."; \
		$(MAKE) -C $$dir clean-chart; \
	done

clean:
	echo "Cleaning all projects..."	
	@for dir in $(PROJECTS); do \
		echo "Running make clean in $$dir..."; \
		$(MAKE) -C $$dir clean; \
	done

push:
	echo "Pushing all projects..."
	@for dir in $(PROJECTS); do \
		echo "Running make publish-image in $$dir..."; \
		$(MAKE) -C $$dir publish-image; \
	done

static-code-analysis:
	echo "Running static code analysis for all projects..."
	@for dir in $(PROJECTS); do \
		echo "Running make static-code-analysis in $$dir..."; \
		$(MAKE) -C $$dir static-code-analysis; \
	done

tests:
	echo "Running tests for all projects..."
	@for dir in $(PROJECTS); do \
		echo "Running make tests in $$dir..."; \
		$(MAKE) -C $$dir tests; \
	done

test-unit:
	echo "Running unit tests for all projects..."
	@for dir in $(PROJECTS); do \
		echo "Running make test-unit in $$dir..."; \
		$(MAKE) -C $$dir test-unit; \
	done

test-integration:
	echo "Running integration tests for all projects..."
	@for dir in $(PROJECTS); do \
		echo "Running make test-integration in $$dir..."; \
		$(MAKE) -C $$dir test-integration; \
	done	

test-component:
	echo "Running component tests for all projects..."
	@for dir in $(PROJECTS); do \
		echo "Running make test-component in $$dir..."; \
		$(MAKE) -C $$dir test-component; \
	done
