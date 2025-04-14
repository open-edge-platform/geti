# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum

import pytest
from opentelemetry.sdk.metrics.export import AggregationTemporality, InMemoryMetricReader  # type: ignore

from geti_telemetry_tools.metrics.instruments import (
    EmptyInstrumentAttributes,
    ModelExportsCounterAttributes,
    images_resolution_histogram,
    in_memory_metric_reader,
    meter,
    model_exports_counter,
    videos_frames_histogram,
    videos_resolution_histogram,
)


class DummyTaskType(Enum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"
    ANOMALY_DETECTION = "anomaly_detection"


@pytest.fixture
def fxt_metric_reader_for_testing() -> InMemoryMetricReader:
    if in_memory_metric_reader is None:
        raise RuntimeError("Test metric reader not initialized")
    return in_memory_metric_reader


class TestMetricsInstruments:
    def test_images_resolution_histogram(self, fxt_metric_reader_for_testing) -> None:
        assert images_resolution_histogram.name == "geti.application.media.size.images.resolution"
        assert images_resolution_histogram.unit == "MP"

        # Verify that adding records does not throw errors
        images_resolution_histogram.record(3, EmptyInstrumentAttributes().to_dict())
        images_resolution_histogram.record(15, EmptyInstrumentAttributes().to_dict())
        images_resolution_histogram.record(8, EmptyInstrumentAttributes().to_dict())

        # Verify the data
        metrics_data = fxt_metric_reader_for_testing.get_metrics_data()
        scope_metrics = next(sm for sm in metrics_data.resource_metrics[0].scope_metrics if sm.scope.name == meter.name)
        image_res_metric_data = next(m for m in scope_metrics.metrics if m.name == images_resolution_histogram.name)
        assert image_res_metric_data.unit == images_resolution_histogram.unit
        assert image_res_metric_data.data.aggregation_temporality == AggregationTemporality.CUMULATIVE
        datapoints = image_res_metric_data.data.data_points
        assert len(datapoints) == 1
        assert datapoints[0].attributes == {}
        assert datapoints[0].explicit_bounds == (1, 10, 50)
        assert datapoints[0].count == 3  # 3 records
        assert datapoints[0].bucket_counts == (0, 2, 1, 0)  # 2 records in (1,10], 1 in (10,50]
        assert datapoints[0].min == 3
        assert datapoints[0].max == 15

    def test_videos_frames_histogram(self, fxt_metric_reader_for_testing) -> None:
        assert videos_frames_histogram.name == "geti.application.media.size.videos.frames"
        assert videos_frames_histogram.unit == "1"

        # Verify that adding a record does not throw errors
        videos_frames_histogram.record(10000, EmptyInstrumentAttributes().to_dict())
        videos_frames_histogram.record(3000, EmptyInstrumentAttributes().to_dict())
        videos_frames_histogram.record(15000, EmptyInstrumentAttributes().to_dict())

        # Verify the data
        metrics_data = fxt_metric_reader_for_testing.get_metrics_data()
        scope_metrics = next(sm for sm in metrics_data.resource_metrics[0].scope_metrics if sm.scope.name == meter.name)
        video_frames_metric_data = next(m for m in scope_metrics.metrics if m.name == videos_frames_histogram.name)
        assert video_frames_metric_data.unit == videos_frames_histogram.unit
        assert video_frames_metric_data.data.aggregation_temporality == AggregationTemporality.CUMULATIVE
        datapoints = video_frames_metric_data.data.data_points
        assert len(datapoints) == 1
        assert datapoints[0].attributes == {}
        assert datapoints[0].explicit_bounds == (1000, 10000, 100000)
        assert datapoints[0].count == 3
        assert datapoints[0].bucket_counts == (0, 2, 1, 0)
        assert datapoints[0].min == 3000
        assert datapoints[0].max == 15000

    def test_videos_resolution_histogram(self, fxt_metric_reader_for_testing) -> None:
        assert videos_resolution_histogram.name == "geti.application.media.size.videos.resolution"
        assert videos_resolution_histogram.unit == "MP"

        # Verify that adding a record does not throw errors
        videos_resolution_histogram.record(3, EmptyInstrumentAttributes().to_dict())
        videos_resolution_histogram.record(0.1, EmptyInstrumentAttributes().to_dict())
        videos_resolution_histogram.record(0.5, EmptyInstrumentAttributes().to_dict())

        # Verify the data
        metrics_data = fxt_metric_reader_for_testing.get_metrics_data()
        scope_metrics = next(sm for sm in metrics_data.resource_metrics[0].scope_metrics if sm.scope.name == meter.name)
        video_res_metric_data = next(m for m in scope_metrics.metrics if m.name == videos_resolution_histogram.name)
        assert video_res_metric_data.unit == videos_resolution_histogram.unit
        assert video_res_metric_data.data.aggregation_temporality == AggregationTemporality.CUMULATIVE
        datapoints = video_res_metric_data.data.data_points
        assert len(datapoints) == 1
        assert datapoints[0].attributes == {}
        assert datapoints[0].explicit_bounds == (0.25, 0.6, 1.5, 5)
        assert datapoints[0].count == 3
        assert datapoints[0].bucket_counts == (1, 1, 0, 1, 0)
        assert datapoints[0].min == 0.1
        assert datapoints[0].max == 3

    def test_model_exports_counter_attr(self) -> None:
        attr = ModelExportsCounterAttributes(
            model_architecture="SSD",
            format="OPENVINO",
            precision="FP32",
        )
        attr_dict = attr.to_dict()

        assert attr_dict == {
            "model_architecture": "SSD",
            "format": "OPENVINO",
            "precision": "FP32",
        }

    def test_model_exports_counter(self, fxt_metric_reader_for_testing) -> None:
        assert model_exports_counter.name == "geti.application.models.exports.count"
        assert model_exports_counter.unit == "1"
        attributes = ModelExportsCounterAttributes(
            model_architecture="SSD",
            format="OPENVINO",
            precision="FP32",
        ).to_dict()

        # Verify that incrementing the counter does not throw errors
        model_exports_counter.add(1, attributes)
        model_exports_counter.add(3, attributes)

        # Verify the data
        metrics_data = fxt_metric_reader_for_testing.get_metrics_data()
        scope_metrics = next(sm for sm in metrics_data.resource_metrics[0].scope_metrics if sm.scope.name == meter.name)
        export_metric_data = next(m for m in scope_metrics.metrics if m.name == model_exports_counter.name)
        assert export_metric_data.unit == model_exports_counter.unit
        assert export_metric_data.data.aggregation_temporality == AggregationTemporality.CUMULATIVE
        datapoints = export_metric_data.data.data_points
        assert len(datapoints) == 1
        assert datapoints[0].attributes == attributes
        assert datapoints[0].value == 4  # 1 plus 3`
