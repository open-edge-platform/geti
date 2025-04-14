# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


"""
This module is responsible for executing flow control tasks.
"""

import logging

from sc_sdk.algorithms.crop.task import CropTask
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.label_schema import LabelSchema
from sc_sdk.entities.model import NullModel
from sc_sdk.entities.model_template import TaskType
from sc_sdk.entities.project import Project
from sc_sdk.entities.subset import Subset
from sc_sdk.entities.task_environment import TaskEnvironment
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import LabelSchemaRepo
from sc_sdk.services import ModelService

logger = logging.getLogger(__name__)


class FlowControl:
    """
    This class is responsible for performing flow control operations on a dataset.
    """

    @staticmethod
    def __crop(
        project: Project,
        crop_task_node: TaskNode,
        source_task_node: TaskNode,
        dataset: Dataset,
        label_schema: LabelSchema | None = None,
        subset: Subset | None = None,
    ) -> Dataset:
        """
        Crop a dataset by means of a :class:`CropTask`.

        The new dataset is built out of the elements of the input dataset which
        contain labels belonging to the given source task.

        :param project: Project the nodes belong to
        :param crop_task_node: The task node defining the crop operation.
        :param source_task_node: Task which provides the the dataset to crop. In a
            pipeline project, this is typically the node immediately before the crop one
        :param dataset: Dataset to crop
        :param label_schema: LabelSchema to use for cropping.
            If unspecified, it is extracted from the dataset (if present) or the source task node.
        :param subset: Subset to set to the new dataset items. If set to none, the crop task will set the subset.
        :return: Cropped dataset
        """
        # Load the label schema
        if label_schema is None:
            if dataset.label_schema_id:
                logger.debug(f"'crop' will load the label schema of dataset {dataset.label_schema_id} on-the-fly")
                label_schema = LabelSchemaRepo(project.identifier).get_by_id(dataset.label_schema_id)
            else:
                logger.debug(f"'crop' will load the latest label schema of task {source_task_node.id_} on-the-fly")
                label_schema = LabelSchemaRepo(project.identifier).get_latest_view_by_task(
                    task_node_id=source_task_node.id_
                )

        model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier, task_node_id=crop_task_node.id_
        )
        task_environment = TaskEnvironment(
            model_template=model_storage.model_template,
            model=NullModel(),
            hyper_parameters=ConfigurableParameters(header="Empty parameters"),  # type: ignore
            label_schema=label_schema,
        )
        crop_task = CropTask(task_environment=task_environment)
        return crop_task.infer(dataset=dataset, subset=subset)

    @staticmethod
    def flow_control(
        project: Project,
        task_node: TaskNode,
        dataset: Dataset,
        prev_task_node: TaskNode | None = None,
        label_schema: LabelSchema | None = None,
        subset: Subset | None = None,
    ) -> Dataset:
        """
        Performs the flow control operation defined by task_node on the provided dataset

        :param project: Project the nodes belong to
        :param task_node: The task node defining the flow control operation to perform
        :param dataset: Dataset on which to apply the flow control operation
        :param prev_task_node: The task node which is the immediate predecessor of
            task_node in the task graph. It is required by some flow control operations.
        :param label_schema: Optional, LabelSchema to use for flow control.
        :param subset: Subset to set to the new dataset items. If set to none, the flow control
         task will set the subset.

        :return: dataset after applying flow control
        """
        task_type = task_node.task_properties.task_type
        logger.debug(
            "Flow control task '%s': the input dataset contains %d items",
            task_node.title,
            len(dataset),
        )
        if task_type == TaskType.CROP:
            if prev_task_node is None:
                raise ValueError(f"Cannot crop (task {task_node.id_}) without a predecessor task node")
            dataset = FlowControl.__crop(
                project=project,
                crop_task_node=task_node,
                source_task_node=prev_task_node,
                dataset=dataset,
                label_schema=label_schema,
                subset=subset,
            )
        else:
            raise NotImplementedError(f"Flow control task with title '{task_node.title}' is not supported")
        logger.debug(
            "Flow control task '%s': the output dataset contains %d items",
            task_node.title,
            len(dataset),
        )
        return dataset
