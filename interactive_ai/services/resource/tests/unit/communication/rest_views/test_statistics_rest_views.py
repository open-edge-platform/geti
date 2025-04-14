# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from testfixtures import compare

from communication.rest_views.statistics_rest_views import StatisticsRESTViews

from sc_sdk.entities.metrics import BarChartInfo, BarMetricsGroup, TextChartInfo, TextMetricsGroup


class TestStatisticsRESTViews:
    def test_text_chart_metrics_group_to_rest(
        self,
        fxt_text_metrics_group_with_duration,
        fxt_text_metrics_group_with_duration_rest,
    ):
        result = StatisticsRESTViews.metrics_groups_to_rest([fxt_text_metrics_group_with_duration], labels=[])
        compare(result, [fxt_text_metrics_group_with_duration_rest], ignore_eq=True)

    def test_bar_chart_metrics_group_to_rest(self, fxt_bar_metrics_group, fxt_bar_metrics_group_rest, fxt_label):
        result = StatisticsRESTViews.metrics_groups_to_rest([fxt_bar_metrics_group], labels=[fxt_label])
        compare(result, [fxt_bar_metrics_group_rest], ignore_eq=True)

    def test_bar_chart_metrics_group_per_label_to_rest(
        self,
        fxt_bar_metrics_group_per_label,
        fxt_bar_metrics_group_per_label_rest,
        fxt_label,
    ):
        result = StatisticsRESTViews.metrics_groups_to_rest([fxt_bar_metrics_group_per_label], labels=[fxt_label])
        compare(result, [fxt_bar_metrics_group_per_label_rest], ignore_eq=True)

    def test_line_chart_metrics_group_to_rest(
        self, fxt_line_chart_metric_group, fxt_line_chart_metric_group_rest, fxt_label
    ):
        result = StatisticsRESTViews.metrics_groups_to_rest([fxt_line_chart_metric_group], [fxt_label])
        compare(result, [fxt_line_chart_metric_group_rest], ignore_eq=True)

    def test_line_chart_metrics_group_with_nan_to_rest(
        self,
        fxt_line_chart_metric_group_with_nan,
        fxt_line_chart_metric_after_nan_group_rest,
        fxt_label,
    ):
        result = StatisticsRESTViews.metrics_groups_to_rest([fxt_line_chart_metric_group_with_nan], [fxt_label])
        compare(result, [fxt_line_chart_metric_after_nan_group_rest], ignore_eq=True)

    def test_line_chart_metrics_group_per_label_to_rest(
        self,
        fxt_line_chart_metric_group_per_label,
        fxt_line_chart_metric_group_rest_per_label,
        fxt_label,
    ):
        result = StatisticsRESTViews.metrics_groups_to_rest([fxt_line_chart_metric_group_per_label], [fxt_label])
        compare(result, [fxt_line_chart_metric_group_rest_per_label], ignore_eq=True)

    def test_matrix_chart_metrics_group_to_rest(self, fxt_matrix_metrics_group, fxt_matrix_metrics_group_rest):
        result = StatisticsRESTViews.matrix_chart_metrics_group_to_rest(fxt_matrix_metrics_group)
        compare(result, fxt_matrix_metrics_group_rest, ignore_eq=True)

    def test_duration_metric_to_rest(self, fxt_duration_metric, fxt_duration_metric_rest):
        result = StatisticsRESTViews.duration_metric_to_rest(fxt_duration_metric)
        compare(result, fxt_duration_metric_rest, ignore_eq=True)

    def test_date_metric_to_rest(self, fxt_date_metric, fxt_date_metric_rest):
        result = StatisticsRESTViews.text_chart_metrics_group_to_rest(
            TextMetricsGroup([fxt_date_metric], TextChartInfo(""))
        )
        compare(result["value"], fxt_date_metric_rest, ignore_eq=True)

    def test_score_metric_to_rest(self, fxt_score_metric, fxt_score_metric_rest):
        result = StatisticsRESTViews.text_chart_metrics_group_to_rest(
            TextMetricsGroup([fxt_score_metric], TextChartInfo(""))
        )
        compare(result["value"], fxt_score_metric_rest, ignore_eq=True)

    def test_count_metric_to_rest(self, fxt_count_metric, fxt_count_metric_rest):
        result = StatisticsRESTViews.text_chart_metrics_group_to_rest(
            TextMetricsGroup([fxt_count_metric], TextChartInfo(""))
        )
        compare(result["value"], fxt_count_metric_rest, ignore_eq=True)

    def test_bar_chart_count_metric_to_rest(self, fxt_count_metric, fxt_count_metric_rest):
        result = StatisticsRESTViews.bar_chart_metrics_group_to_rest(
            BarMetricsGroup([fxt_count_metric], BarChartInfo("")), labels=[]
        )
        compare(result["value"][0]["value"], fxt_count_metric_rest, ignore_eq=True)

    def test_string_metric_to_rest(self, fxt_string_metric, fxt_string_metric_rest):
        result = StatisticsRESTViews.text_chart_metrics_group_to_rest(
            TextMetricsGroup([fxt_string_metric], TextChartInfo(""))
        )
        compare(result["value"], fxt_string_metric_rest, ignore_eq=True)

    def test_curve_metric_to_rest(self, fxt_curve_metric, fxt_curve_metric_rest, fxt_label):
        result = StatisticsRESTViews.curve_metric_to_rest(fxt_curve_metric, labels=[fxt_label], per_label=False)
        compare(result, fxt_curve_metric_rest, ignore_eq=True)

    def test_matrix_metric_to_rest(self, fxt_matrix_metric, fxt_matrix_metric_rest):
        result = StatisticsRESTViews.matrix_metric_to_rest(fxt_matrix_metric)
        compare(result, fxt_matrix_metric_rest, ignore_eq=True)

    def test_matrix_metric_group_to_rest(self, fxt_matrix_metrics_group, fxt_matrix_metrics_group_rest):
        result = StatisticsRESTViews.metrics_groups_to_rest([fxt_matrix_metrics_group], [])
        compare(result, [fxt_matrix_metrics_group_rest], ignore_eq=True)

    def test_null_metrics_groups_to_rest(self, fxt_null_metric_group):
        empty_result = StatisticsRESTViews.metrics_groups_to_rest([fxt_null_metric_group], labels=[])
        compare(empty_result, [], ignore_eq=True)

    def test_invalid_bar_chart_metric(self, fxt_string_metric):
        invalid_metric = BarMetricsGroup(metrics=[fxt_string_metric], visualization_info=BarChartInfo(""))
        with pytest.raises(NotImplementedError):
            StatisticsRESTViews.bar_chart_metrics_group_to_rest(invalid_metric, labels=[])
