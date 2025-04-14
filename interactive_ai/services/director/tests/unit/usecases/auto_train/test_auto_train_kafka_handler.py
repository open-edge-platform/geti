# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
from unittest.mock import patch

import pytest
from tests.unit.mocked_method_helpers import return_none

from usecases.auto_train import AutoTrainUseCase
from usecases.auto_train.kafka_handler import AutoTrainingKafkaHandler

from geti_kafka_tools import KafkaRawMessage


@pytest.fixture
def fxt_consumer_record_maker():
    def _make_record(value):
        return KafkaRawMessage(
            topic="fxt_consumer_record",
            partition=0,
            offset=0,
            timestamp=int(datetime.datetime.now().timestamp()),
            timestamp_type=0,
            key="",
            value=value,
            headers=[
                ("organization_id", b"000000000000000000000001"),
                ("workspace_id", b"63b183d00000000000000001"),
                ("source", b"browser"),
            ],
        )

    yield _make_record


@pytest.fixture
def fxt_auto_train_kafka_handler():
    with patch.object(AutoTrainingKafkaHandler, "__init__", new=return_none):
        auto_train_kafka_handler = AutoTrainingKafkaHandler()
        auto_train_kafka_handler.auto_train_use_case = AutoTrainUseCase()
        yield auto_train_kafka_handler


class TestAutoTrainKafkaHandler:
    def test_on_configuration_changed(
        self, fxt_project_identifier, fxt_consumer_record_maker, fxt_auto_train_kafka_handler
    ):
        value = {
            "workspace_id": str(fxt_project_identifier.workspace_id),
            "project_id": str(fxt_project_identifier.project_id),
        }
        record_consumer = fxt_consumer_record_maker(value)

        with patch.object(AutoTrainUseCase, "on_configuration_changed", return_value=None) as patched_usecase_handler:
            fxt_auto_train_kafka_handler.on_configuration_changed(record_consumer)

        assert patched_usecase_handler.called_once_with(project_identifier=fxt_project_identifier)

    def test_on_dataset_counters_updated(
        self, fxt_project_identifier, fxt_consumer_record_maker, fxt_auto_train_kafka_handler
    ):
        value = {
            "workspace_id": str(fxt_project_identifier.workspace_id),
            "project_id": str(fxt_project_identifier.project_id),
        }
        record_consumer = fxt_consumer_record_maker(value)

        with patch.object(
            AutoTrainUseCase, "on_dataset_counters_updated", return_value=None
        ) as patched_usecase_handler:
            fxt_auto_train_kafka_handler.on_dataset_counters_updated(record_consumer)

        assert patched_usecase_handler.called_once_with(project_identifier=fxt_project_identifier)

    def test_on_training_successful(
        self, fxt_project_identifier, fxt_consumer_record_maker, fxt_auto_train_kafka_handler
    ):
        value = {
            "workspace_id": str(fxt_project_identifier.workspace_id),
            "project_id": str(fxt_project_identifier.project_id),
        }
        record_consumer = fxt_consumer_record_maker(value)

        with patch.object(AutoTrainUseCase, "on_training_successful", return_value=None) as patched_usecase_handler:
            fxt_auto_train_kafka_handler.on_training_successful(record_consumer)

        assert patched_usecase_handler.called_once_with(project_identifier=fxt_project_identifier)
