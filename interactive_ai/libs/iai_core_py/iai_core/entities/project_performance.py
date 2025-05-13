# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ProjectPerformance and related classes"""

from dataclasses import dataclass

from iai_core.entities.metrics import AnomalyLocalizationPerformance, Performance

from geti_types import ID


@dataclass
class TaskPerformanceScore:
    """
    TaskPerformanceScore stores the value and metric type of score

    :param value: float value of the score
    :param metric_type: the name/description of the type of the score value
    """

    value: float
    metric_type: str


class TaskPerformance:
    """
    TaskPerformance stores the score of the current active model.

    :param task_node_id: ID of the task node
    :param score: TaskPerformanceScore that has the value and the metric type of the score
    """

    def __init__(
        self,
        task_node_id: ID,
        score: TaskPerformanceScore | None = None,
    ) -> None:
        self.task_node_id = task_node_id
        self._score = score

    @property
    def score(self) -> TaskPerformanceScore | None:
        return self._score

    def __repr__(self) -> str:
        return f"TaskPerformance(task_node_id={self.task_node_id}, score={self.score})"


class GlobalLocalTaskPerformance(TaskPerformance):
    """
    GlobalLocalTaskPerformance stores the global and local score of the current active model.

    This class stores the performance for anomaly localization tasks, which have a global
    and a local score. The global score is also mapped to the score attribute of a basic
    TaskPerformance.

    :param task_node_id: ID of the task node
    :param global_score: TaskPerformanceScore that has the value and the metric type of
        the image level score
    :param local_score: TaskPerformanceScore that has the value and the metric type of
        the pixel (segmentation) or bounding box (detection) score
    """

    def __init__(
        self,
        task_node_id: ID,
        global_score: TaskPerformanceScore,
        local_score: TaskPerformanceScore | None = None,
    ) -> None:
        super().__init__(task_node_id=task_node_id, score=global_score)
        self._local_score = local_score

    @property
    def global_score(self) -> TaskPerformanceScore | None:
        return self._score

    @property
    def local_score(self) -> TaskPerformanceScore | None:
        return self._local_score

    def __repr__(self) -> str:
        return (
            f"GlobalLocalTaskPerformance(task_node_id={self.task_node_id}, "
            f"global_score={self.global_score}, local_score={self.local_score})"
        )


class ProjectPerformance:
    """
    ProjectPerformance stores the current project score and task performances for each
    trainable task in the project.

    :param task_performances: list of TaskPerformance for each trainable task node
    :param score: current project score of the project
    """

    def __init__(self, task_performances: list[TaskPerformance], score: float | None = None) -> None:
        self._score = score
        self._task_performances = {
            task_performance.task_node_id: task_performance for task_performance in task_performances
        }

    @property
    def score(self) -> float | None:
        return self._score

    @property
    def task_performances(self) -> dict[ID, TaskPerformance]:
        return self._task_performances

    def update_task_performance(self, task_node_id: ID, model_performance: Performance) -> None:
        """Update task performance and project score using the latest active model Performance for a task."""
        task_performance = self._task_performances.get(task_node_id, None)
        if task_performance is None:
            raise ValueError(f"Project does not have a trainable task with ID: `{task_node_id}`")
        self.task_performances[task_node_id] = self._get_task_performance(
            task_node_id=task_node_id, performance=model_performance
        )

        scores = [
            task_performance.score.value
            for task_performance in self._task_performances.values()
            if task_performance.score is not None
        ]
        if scores:
            self._score = sum(scores) / len(scores)
        else:
            self._score = None

    def _get_task_performance(self, task_node_id: ID, performance: Performance) -> TaskPerformance:
        """Get a new task performance using the latest active model Performance."""
        task_performance: TaskPerformance
        if isinstance(performance, AnomalyLocalizationPerformance):
            global_score = TaskPerformanceScore(
                value=performance.global_score.value,
                metric_type=performance.global_score.name,
            )
            local_score = None
            if performance.local_score is not None:
                local_score = TaskPerformanceScore(
                    value=performance.local_score.value,
                    metric_type=performance.local_score.name,
                )
            task_performance = GlobalLocalTaskPerformance(
                task_node_id=task_node_id,
                global_score=global_score,
                local_score=local_score,
            )
        else:
            score = TaskPerformanceScore(
                value=performance.score.value,
                metric_type=performance.score.name,
            )
            task_performance = TaskPerformance(task_node_id=task_node_id, score=score)
        return task_performance

    def __repr__(self) -> str:
        return f"ProjectPerformance(score={self.score}, task_performances={self.task_performances.values()})"
