# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Metric entities."""

import abc
import datetime
import logging
import math
from collections.abc import Sequence
from enum import Enum
from typing import Generic, TypeVar

import numpy as np

from geti_types import ID

logger = logging.getLogger(__name__)


class MetricEntity(metaclass=abc.ABCMeta):
    """
    This interface represents a metric, which is the smallest building block for the performance statistics.

    It only contains the name of the metric.
    See also :class:`MetricsGroup` and :class:`Performance` for the structure of performance statistics.
    """

    __name = ""

    @property
    def name(self) -> str:
        """Returns the name of the Metric Entity."""
        return self.__name

    @name.setter
    def name(self, value: str):
        self.__name = value

    @staticmethod
    @abc.abstractmethod
    def type() -> str:
        """Returns the type of the MetricEntity, e.g. "curve."""


class CountMetric(MetricEntity):
    """
    This metric represents an integer-valued count.

    :param name: The name of the metric
    :param value: The value of the metric

    Example:
        The count for number of images in a project

    >>> count_metric = CountMetric(name="Number of images", value=20)

    """

    value: int

    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "count"

    def __eq__(self, other: object) -> bool:
        """Returns True if the metrics are equal."""
        if not isinstance(other, CountMetric):
            return False
        return self.name == other.name and self.value == other.value


class StringMetric(MetricEntity):
    """
    This metric represents a string value.

    :param name: The name of the info metric
    :param value: The info of the metric

    Example:
        An info metric of training from scratch

    >>> string_metric = StringMetric(name="Model info", value="This model is trained from scratch")

    """

    value: str

    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "string"

    def __eq__(self, other: object) -> bool:
        """Returns True if the metrics are equal."""
        if not isinstance(other, StringMetric):
            return False
        return self.name == other.name and self.value == other.value


class DateMetric(MetricEntity):
    """
    This metric represents a date time value.

    :param name: The name of the date metric
    :param value: The date of the metric

    Example:
        A DateMetric for model creation date (e.g., now).

    >>> metric = DateMetric(name="Model creation", value=datetime.datetime.now(datetime.timezone.utc))

    """

    def __init__(self, name: str, value: datetime.datetime | None = None):
        self.name = name
        if value is None:
            value = datetime.datetime.now(datetime.timezone.utc)
        self.value = value

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "date"

    @property
    def date(self) -> datetime.datetime:
        """Returns the date of the metric."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Returns True if the metrics are equal."""
        if not isinstance(other, DateMetric):
            return False
        return self.name == other.name and self.value == other.value


class ScoreMetric(MetricEntity):
    """
    This metric represents a float value.

    This metric is typically used for storing performance metrics, such as accuracy, f-measure, dice score, etc.

    :param name: The name of the score
    :param value: The value of the score

    Example:
        Accuracy of a model

    >>> score_metric = ScoreMetric(name="Model accuracy", value=0.5)

    """

    def __init__(self, name: str, value: float, label_id: ID | None = None):
        self.name = name
        self.value = value
        self.label_id = label_id

        if math.isnan(value):
            raise ValueError("The value of a ScoreMetric is not allowed to be NaN.")

    @property
    def score(self) -> float:
        return self.value

    def __eq__(self, other: object) -> bool:
        """Returns True if the score metrics are equal."""
        if not isinstance(other, ScoreMetric):
            return False
        return self.name == other.name and self.value == other.value and self.label_id == other.label_id

    def __repr__(self):
        """Returns the representation of the score metric."""
        label_str = f", label_id=`{self.label_id}`" if self.label_id else ""
        return f"ScoreMetric(name=`{self.name}`, score=`{self.value}`{label_str})"

    def __hash__(self):
        return hash((self.name, self.label_id))

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "score"


class NullScoreMetric(ScoreMetric):
    """Represents 'score metric not found'."""

    def __init__(self):
        super().__init__(name="NullScoreMetric", value=0.0)

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "null_score"


class DurationMetric(MetricEntity):
    """
    This metric represents a duration metric, which include hour (int), minute (int), and second (float).

    Example:
        Creating a metric for training duration of 1 hour 5 minutes.

    >>> duration_metric = DurationMetric(name="Training duration", hour=1, minute=5, second=0)

    :param name: The name of the duration metric
    :param hour: The hour value of the metric
    :param minute: The minute value of the metric
    :param second: The second value of the metric
    """

    def __init__(self, name: str, hour: int, minute: int, second: float):
        self.hour = hour
        self.minute = minute
        self.second = second
        self.name = name

    def get_duration_string(self) -> str:
        """Returns the string representation of the duration.

        Example:
            Duration string of 1 hour 1 minute and 1.50 seconds.

        >>> from iai_core_py.entities.metrics import DurationMetric
        >>> dur_met = DurationMetric("test", 1, 1, 1.5)  # 1 hour 1 minute and 1.5 seconds
        >>> dur_met.get_duration_string()
        '1 hour 1 minute 1.50 seconds'

        :return: the string representation of the duration.
        """
        output: str = ""
        if self.hour != 0:
            output += f"{self.hour} hour{'s ' if self.hour > 1 else ' '}"
        if self.minute != 0:
            output += f"{self.minute} minute{'s ' if self.minute > 1 else ' '}"
        if self.second != 0:
            output += f"{self.second:.02f} second{'s ' if self.second > 1 else ' '}"
        return output.strip()

    @staticmethod
    def from_seconds(name: str, seconds: float) -> "DurationMetric":
        """Returns a duration metrics, with name and converted durations from seconds.

        Example:
            Converting 70 seconds to duration metric.

        >>> from iai_core_py.entities.metrics import DurationMetric
        >>> dur_met = DurationMetric.from_seconds("test", 70)  # 1 hour 1 minute and 1.5 seconds
        >>> dur_met.get_duration_string()
        '1 minute 10.00 seconds'

        :param name: name of the duration metric
        :param seconds: number of seconds
        :return: the duration metric with name and converted durations from seconds.
        """
        hour = int(seconds // 3600)
        modulo = seconds % 3600
        minute = int(modulo // 60)
        second = modulo % 60
        return DurationMetric(name=name, hour=hour, minute=minute, second=second)

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "duration"


class CurveMetric(MetricEntity):
    """
    This metric represents a curve. The coordinates are represented as x and y lists.

    Example:
        A line curve of: [(0,1), (1, 5), (2, 8)]

    >>> CurveMetric("Line", xs=[0, 1, 2], ys=[1, 5, 8])
    CurveMetric(name=`Line`, ys=(3 values), xs=(3 values))

    A curve can also be defined only using the y values. For example, a loss curve of loss values: [0.5, 0.2, 0.1].
    The x values will be automatically generated as a 1-based index (1, 2, 3, ...)

    >>> CurveMetric("Loss", ys=[0.5, 0.2, 0.1])
    CurveMetric(name=`Loss`, ys=(3 values), xs=(None values))

    :param name: The name of the curve
    :param xs: the list of floats in x-axis
    :param ys: the list of floats in y-axis
    """

    def __init__(self, name: str, ys: list[float], xs: list[float] | None = None):
        self.name = name
        self.__ys = ys
        if xs is not None:
            if len(xs) != len(self.__ys):
                raise ValueError(f"Curve error must contain the same length for x and y: ({len(xs)} vs {len(self.ys)})")
            self.__xs = xs
        else:
            # if x values are not provided, set them to the 1-index of the y values
            self.__xs = list(range(1, len(self.__ys) + 1))

    @property
    def ys(self) -> list[float]:
        """Returns the list of floats on y-axis."""
        return self.__ys

    @property
    def xs(self) -> list[float]:
        """Returns the list of floats on x-axis."""
        return self.__xs

    def __repr__(self):
        """Returns the string representation of the object."""
        return (
            f"CurveMetric(name=`{self.name}`, ys=({len(self.ys)} values), "
            f"xs=({len(self.xs) if self.xs is not None else 'None'} values))"
        )

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "curve"

    def __eq__(self, other: object) -> bool:
        """Returns True if the metrics are equal."""
        if not isinstance(other, CurveMetric):
            return False
        return self.name == other.name and self.xs == other.xs and self.ys == other.ys


class MatrixMetric(MetricEntity):
    """
    This metric represents a matrix. The cells are represented as a list of lists of integers.

    In the case of a confusion matrix, the rows represent the ground truth items and the columns represent the
    predicted items.

    Example:
        A matrix of: [[4,0,1], [0,3,2], [1,2,2]]

        >>> MatrixMetric("Confusion Matrix", matrix_values=np.array([[4,0,1], [0,3,2], [1,2,2]]))
        MatrixMetric(name=`Confusion Matrix`, matrix_values=(3x3) matrix, row labels=None, column labels=None)

    :param name: The name of the matrix
    :param matrix_values: the matrix data
    :param row_labels: labels for the rows
    :param column_labels: labels for the columns
    :param normalize: set to True to normalize each row of the matrix
    """

    __row_labels: list[str] | None = None
    __column_labels: list[str] | None = None

    # pylint: disable=too-many-arguments; Requires refactor
    def __init__(
        self,
        name: str,
        matrix_values: np.ndarray,
        row_labels: list[str] | None = None,
        column_labels: list[str] | None = None,
        normalize: bool = False,
    ):
        self.name = name
        self.__matrix_values = matrix_values
        self.__matrix_values.astype(np.float32)

        if row_labels is not None:
            self.__row_labels = row_labels
            if self.__matrix_values.shape[0] != len(self.__row_labels):
                raise ValueError(
                    f"Number of rows of the matrix and number of row labels must be equal. The shape "
                    f"has {self.__matrix_values.shape[0]} rows and {len(self.__row_labels)} row labels"
                )

        if column_labels is not None:
            self.__column_labels = column_labels
            if self.__matrix_values.shape[1] != len(self.__column_labels):
                raise ValueError(
                    f"Number of columns of the matrix and number of column labels must be equal. The "
                    f"shape has {self.__matrix_values.shape[1]} columns and {len(self.__column_labels)} column "
                    "labels"
                )

        if normalize:
            self.normalize()

    @property
    def matrix_values(self) -> np.ndarray:
        """Returns the matrix data."""
        return self.__matrix_values

    @property
    def row_labels(self) -> list[str] | None:
        """Returns the row labels."""
        return self.__row_labels

    @property
    def column_labels(self) -> list[str] | None:
        """Returns the column labels."""
        return self.__column_labels

    def normalize(self) -> None:
        """Normalizes the confusion matrix by dividing by the sum of the rows."""
        self.__matrix_values = self.__matrix_values.astype(np.float32) / self.__matrix_values.astype(np.float32).sum(
            axis=1, keepdims=True
        )  # Divide all values by the sum of its row

        if not np.all(self.__matrix_values.sum(axis=1, keepdims=True) > 0):
            self.__matrix_values = np.nan_to_num(self.__matrix_values)

            logger.warning("Replacing NaN in the matrix with zeroes since the sum of one (or more) row(s) was zero.")

    def __repr__(self):
        """Returns the string representation of the object."""
        return (
            f"MatrixMetric(name=`{self.name}`, matrix_values=({self.__matrix_values.shape[0]}x"
            f"{self.__matrix_values.shape[1]}) matrix, row labels={self.__row_labels}, column labels"
            f"={self.__column_labels})"
        )

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "matrix"

    def __eq__(self, other: object) -> bool:
        """Returns True if the metrics are equal."""
        if not isinstance(other, MatrixMetric):
            return False
        return (
            self.name == other.name
            and np.array_equal(self.matrix_values, other.matrix_values)
            and self.row_labels == other.row_labels
            and self.column_labels == other.column_labels
        )


class NullMetric(MetricEntity):
    """Represents 'Metric not found'."""

    def __init__(self) -> None:
        self.name = "NullMetric"

    def __repr__(self):
        """Returns the string representation of the object."""
        return "NullMetric()"

    def __eq__(self, other: object) -> bool:
        """Returns True if the other object is a NullMetric."""
        return isinstance(other, NullMetric)

    @staticmethod
    def type() -> str:
        """Returns the type of the MetricEntity."""
        return "null"


class VisualizationType(Enum):
    """This enum defines how the metrics will be visualized on the UI."""

    TEXT = 0
    RADIAL_BAR = 1
    BAR = 2
    LINE = 3
    MATRIX = 4


class ColorPalette(Enum):
    """
    Enum class specifying the color palette to be used by the UI to display statistics.

    If the statistics are per label, set to LABEL so the UI will use the label color palette.
    Otherwise, set to DEFAULT (allow the UI to choose a color palette)
    """

    DEFAULT = 0
    LABEL = 1


class VisualizationInfo:
    """This represents the visualization info a metrics group. See :class:`MetricsGroup`."""

    __type: VisualizationType
    name: str  # todo: this should be a part of MetricsGroup, not the visualization info.

    def __init__(
        self,
        name: str,
        visualisation_type: VisualizationType,
        palette: ColorPalette = ColorPalette.DEFAULT,
    ):
        self.__type = visualisation_type
        self.name = name
        self.palette = palette

    @property
    def type(self) -> VisualizationType:
        """Returns the type of the visualization."""
        return self.__type

    def __repr__(self):
        """Returns the string representation of the object."""
        return f"VisualizationInfo(name='{self.name}', type='{self.type.name}', palette='{self.palette.name}')"

    def __eq__(self, other: object) -> bool:
        """Returns True if the metrics are equal."""
        if not isinstance(other, VisualizationInfo):
            return False
        return self.name == other.name and self.type == other.type and self.palette == other.palette


class TextChartInfo(VisualizationInfo):
    """This represents a visualization using text, which uses only a single string."""

    def __init__(
        self,
        name: str,
    ):
        super().__init__(name, VisualizationType.TEXT)

    def __repr__(self):
        """Returns the string representation of the object."""
        return f"TextChartInfo(name='{self.name}, 'type='{self.type}')"


class LineChartInfo(VisualizationInfo):
    """This represents a visualization using a line chart."""

    x_axis_label: str
    y_axis_label: str

    def __init__(
        self,
        name: str,
        x_axis_label: str | None = None,
        y_axis_label: str | None = None,
        palette: ColorPalette = ColorPalette.DEFAULT,
    ):
        super().__init__(name, VisualizationType.LINE, palette)
        if x_axis_label is None:
            x_axis_label = ""
        if y_axis_label is None:
            y_axis_label = ""

        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label

    def __repr__(self):
        """Returns the string representation of the object."""
        return (
            f"LineChartInfo(name='{self.name}, 'type='{self.type}', x_axis_label='{self.x_axis_label}', "
            f"y_axis_label='{self.y_axis_label}')"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LineChartInfo):
            return False
        return (
            super().__eq__(other)
            and self.x_axis_label == other.x_axis_label
            and self.y_axis_label == other.y_axis_label
        )


class BarChartInfo(VisualizationInfo):
    """This represents a visualization using a bar chart."""

    def __init__(
        self,
        name: str,
        palette: ColorPalette = ColorPalette.DEFAULT,
        visualization_type: VisualizationType = VisualizationType.BAR,
    ):
        if visualization_type not in (
            VisualizationType.BAR,
            VisualizationType.RADIAL_BAR,
        ):
            raise ValueError("Visualization type for BarChartInfo must be BAR or RADIAL_BAR")
        super().__init__(name, visualization_type, palette)

    def __repr__(self):
        """Returns the string representation of the object."""
        return f"BarChartInfo(name='{self.name}', type='{self.type}')"


class MatrixChartInfo(VisualizationInfo):
    """This represents a visualization using a matrix."""

    header: str
    row_header: str
    column_header: str

    # pylint: disable=too-many-arguments; Requires refactor
    def __init__(
        self,
        name: str,
        header: str | None = None,
        row_header: str | None = None,
        column_header: str | None = None,
        palette: ColorPalette = ColorPalette.DEFAULT,
    ):
        super().__init__(name, VisualizationType.MATRIX, palette)
        if header is not None:
            self.header = header
        if row_header is not None:
            self.row_header = row_header
        if column_header is not None:
            self.column_header = column_header

    def __repr__(self):
        """Returns the string representation of the object."""
        return (
            f"MatrixChartInfo(name='{self.name}', type='{self.type}', header='{self.header}', row_header='"
            f"{self.row_header}', column_header='{self.column_header}')"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatrixChartInfo):
            return False
        return (
            super().__eq__(other)
            and self.header == other.header
            and self.row_header == other.row_header
            and self.column_header == other.column_header
        )


_Metric = TypeVar("_Metric", bound=MetricEntity)
_VisualizationInfo = TypeVar("_VisualizationInfo", bound=VisualizationInfo)


class MetricsGroup(Generic[_Metric, _VisualizationInfo]):
    """
    This class aggregates a list of metric entities and defines how this group will be visualized on the UI.

    This class is the parent class to the different types of MetricsGroup that each represent a different type of chart
    in the UI.

    Example:
        An accuracy as a metrics group
            >>> acc = ScoreMetric("Accuracy", 0.5)
            >>> visual_info = BarChartInfo("Accuracy", visualization_type=_VisualizationInfo.BAR)  # show as radial bar
            >>> metrics_group = BarMetricsGroup([acc], visual_info)

        Loss curves as a metrics group
            >>> train_loss = CurveMetric("Train loss", xs=[0, 1, 2], ys=[5, 3, 1])
            >>> val_loss = CurveMetric("Validation", xs=[0, 1, 2], ys=[6, 4, 2])
            >>> visual_info = LineChartInfo("Loss curve", x_axis_label="# epoch", y_axis_label="Loss")
            >>> metrics_group = LineMetricsGroup([train_loss, val_loss], visual_info)
    """

    def __init__(self, metrics: Sequence[_Metric], visualization_info: _VisualizationInfo):
        if metrics is None or len(metrics) == 0:
            raise ValueError("Metrics cannot be None or empty")
        if visualization_info is None:
            raise ValueError("visualization_info cannot be None")
        self.metrics = metrics
        self.visualization_info = visualization_info

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MetricsGroup):
            return False
        return self.metrics == other.metrics and self.visualization_info == other.visualization_info


class MatrixMetricsGroup(MetricsGroup[MatrixMetric, MatrixChartInfo]):
    """
    This class represent a matrix chart in the UI.

    Multiple matrices can be displayed in the same chart.
    """

    def __init__(self, metrics: Sequence[MatrixMetric], visualization_info: MatrixChartInfo):
        super().__init__(metrics=metrics, visualization_info=visualization_info)


class LineMetricsGroup(MetricsGroup[CurveMetric, LineChartInfo]):
    """
    This class represent a line chart in the UI.

    Multiple lines can be displayed in a single chart.
    """

    def __init__(self, metrics: Sequence[CurveMetric], visualization_info: LineChartInfo):
        super().__init__(metrics=metrics, visualization_info=visualization_info)


class BarMetricsGroup(MetricsGroup[ScoreMetric | CountMetric, BarChartInfo]):
    """
    This class represent a bar or radial bar chart in the UI.

    Each metric in the metrics group represents the value of a single bar/radial bar in the chart.
    """

    def __init__(
        self,
        metrics: Sequence[ScoreMetric | CountMetric],
        visualization_info: BarChartInfo,
    ):
        super().__init__(metrics=metrics, visualization_info=visualization_info)


class TextMetricsGroup(
    MetricsGroup[ScoreMetric | CountMetric | StringMetric | DateMetric | DurationMetric, TextChartInfo]
):
    """
    This class represent a text chart in the UI.

    Text charts contain only one metric, which can be of type CountMetric, ScoreMetric, DateMetric, DurationMetric or
    InfoMetric.
    """

    def __init__(
        self,
        metrics: Sequence[ScoreMetric | (CountMetric | (StringMetric | (DateMetric | DurationMetric)))],
        visualization_info: TextChartInfo,
    ):
        if not len(metrics) == 1:
            raise ValueError(
                "A text metrics group can contain only a single "
                "ScoreMetric, CountMetric, StringMetric, DateMetric or "
                "DurationMetric."
            )
        super().__init__(metrics=metrics, visualization_info=visualization_info)


class Performance:
    """
    This performance class wraps the statistics of an entity (e.g., Model, EvaluationResult).

    :param score: the performance score. This will be the point of comparison between two performances.
    :param dashboard_metrics: (optional) additional statistics, containing charts, curves, and other additional info.
    """

    def __init__(self, score: ScoreMetric, dashboard_metrics: list[MetricsGroup] | None = None):
        self._score: ScoreMetric = score
        self.dashboard_metrics: list[MetricsGroup] = [] if dashboard_metrics is None else dashboard_metrics

    @property
    def score(self) -> ScoreMetric:
        """Return the score metric."""
        return self._score

    def __eq__(self, other: object) -> bool:
        """Returns True if self and other have the same score and dashboard metrics."""
        if not isinstance(other, Performance):
            return False
        return self.score == other.score

    def __repr__(self):
        """Returns a string representation of the performance."""
        return f"Performance(score: {self.score.value}, dashboard: ({len(self.dashboard_metrics)} metric groups))"


class NullPerformance(Performance):
    """This is used to represent 'Performance not found'."""

    def __init__(self) -> None:
        super().__init__(score=ScoreMetric(name="Null score", value=0.0))

    def __repr__(self):
        """Returns a string representation of the performance."""
        return "NullPerformance()"

    def __eq__(self, other: object) -> bool:
        """Returns True if other is a NullPerformance."""
        return isinstance(other, NullPerformance)


class MultiScorePerformance(Performance):
    """
    This class can be used in tasks where performance is measured by multiple metrics.

    :param primary_score: The main performance score.
    :param additional_scores: List of additional scores. When no primary score is provided,
        the first additional score takes priority as the main project score.
    :param dashboard_metrics: (optional) additional statistics, containing charts, curves, and other additional info.
    """

    def __init__(
        self,
        primary_score: ScoreMetric | None = None,
        additional_scores: list[ScoreMetric] | None = None,
        dashboard_metrics: list[MetricsGroup] | None = None,
    ):
        self._primary_score = NullScoreMetric() if primary_score is None else primary_score
        self._additional_scores: list[ScoreMetric] = [] if additional_scores is None else additional_scores
        self.dashboard_metrics: list[MetricsGroup] = [] if dashboard_metrics is None else dashboard_metrics

        if self.scores:
            super().__init__(self.scores[0], dashboard_metrics)
        else:
            super().__init__(self._primary_score, dashboard_metrics)

    @property
    def primary_score(self) -> ScoreMetric:
        """Return the primary score metric."""
        return self._primary_score

    @primary_score.setter
    def primary_score(self, score: ScoreMetric) -> None:
        self._primary_score = score

    @property
    def additional_scores(self) -> list[ScoreMetric]:
        """Return the additional score metrics."""
        return self._additional_scores

    @additional_scores.setter
    def additional_scores(self, scores: list[ScoreMetric]) -> None:
        self._additional_scores = scores

    @property
    def scores(self) -> list[ScoreMetric]:
        """Return list of all available scores (primary + additional)"""
        if not isinstance(self.primary_score, NullScoreMetric):
            return [self.primary_score, *self.additional_scores]
        return self.additional_scores

    def add_score(self, score: ScoreMetric) -> None:
        """Adds the given as additional score"""
        self._additional_scores.append(score)

    def __eq__(self, other: object) -> bool:
        """Returns True if the other object is a MultiScorePerformance with the same primary and additional scores."""
        if not isinstance(other, MultiScorePerformance):
            return False
        return self.scores == other.scores

    def __repr__(self):
        """Returns the representation of the performance."""
        return (
            f"MultiScorePerformance(score: {self.score}, primary_metric: {self.primary_score}, "
            f"additional_metrics: ({len(self.additional_scores)} metrics), "
            f"dashboard: ({len(self.dashboard_metrics)} metric groups))"
        )


class AnomalyLocalizationPerformance(MultiScorePerformance):
    """
    Anomaly specific MultiScorePerformance.

    This class implements a special case of the MultiScorePerformance, specific for anomaly tasks that perform
    anomaly localization (detection/segmentation), in addition to anomaly classification.

    :param global_score: Image-level performance metric.
    :param local_score: Pixel- or bbox-level performance metric, depending on the task type.
    :param dashboard_metrics: (optional) additional statistics, containing charts, curves, and other additional info.
    """

    def __init__(
        self,
        global_score: ScoreMetric,
        local_score: ScoreMetric | None,
        dashboard_metrics: list[MetricsGroup] | None,
        use_local_score_as_primary: bool = False,
    ):
        additional_scores: list[ScoreMetric] | None
        if use_local_score_as_primary:
            primary_score = local_score
            additional_scores = [global_score]
        else:
            primary_score = global_score
            additional_scores = [local_score] if local_score else None
        super().__init__(
            primary_score=primary_score,
            additional_scores=additional_scores,
            dashboard_metrics=dashboard_metrics,
        )
        self._global_score = global_score
        self._local_score = local_score

    @property
    def global_score(self) -> ScoreMetric:
        """Return the global (image-level) score metric."""
        return self._global_score

    @property
    def local_score(self) -> ScoreMetric | None:
        """Return the local (pixel-/bbox-level) score metric."""
        return self._local_score

    def as_multi_score_performance(self) -> MultiScorePerformance:
        """Returns the performance as a MultiScorePerformance."""
        return MultiScorePerformance(primary_score=self.primary_score, additional_scores=self.additional_scores)
