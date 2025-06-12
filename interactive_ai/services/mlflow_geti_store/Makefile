include ../../../Makefile.shared-python

COMPONENT_NAME := mlflow-geti-store
# TODO CVS-165924 remove this target after fixing the tests
# NOTE: the tests are fully disabled here because they timeout in the CI after repeatedly failing to connect to Kafka
test-integration:
	echo "test-integration is disabled"
	true

publish-chart:
	@echo "Helm-chart ${COMPONENT_NAME} don't need to be uploaded"
