"""
Implements crop task tests
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime, timezone

from iai_core.algorithms.crop.task import CropTask
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.entities.annotation import Annotation
from iai_core.entities.label_schema import LabelGroup, LabelSchema
from iai_core.entities.model import NullModel
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Rectangle
from iai_core.entities.subset import Subset
from iai_core.entities.task_environment import TaskEnvironment


class TestCropTask:
    def test_crop_infer(
        self,
        fxt_ote_id,
        fxt_detection_segmentation_chain_project,
        fxt_single_crate_image_dataset_for_project,
        fxt_label,
        fxt_model_template_detection,
        fxt_segmentation_labels,
    ):
        label_schema = LabelSchema(id_=fxt_ote_id())
        label_detection_group = LabelGroup(labels=[fxt_label], name="dummy detection label group")
        label_schema.add_group(label_detection_group)

        detection_annotation_1 = Annotation(
            shape=Rectangle(
                x1=0.0,
                x2=0.5,
                y1=0.0,
                y2=1.0,
                modification_date=datetime(2021, 7, 15, tzinfo=timezone.utc),
            ),
            labels=[ScoredLabel(label_id=fxt_label.id_, is_empty=fxt_label.is_empty, probability=1.0)],
            id_="92497df6-f45a-11eb-9a03-0242ac130003",
        )
        detection_annotation_2 = Annotation(
            shape=Rectangle(
                x1=0.5,
                x2=1.0,
                y1=0.0,
                y2=1.0,
                modification_date=datetime(2021, 7, 15, tzinfo=timezone.utc),
            ),
            labels=[ScoredLabel(label_id=fxt_label.id_, is_empty=fxt_label.is_empty, probability=1.0)],
            id_="92497df6-f45a-11eb-9a03-0242ac130003",
        )
        segmentation_annotation_1 = Annotation(
            shape=Rectangle(
                x1=0.1,
                x2=0.4,
                y1=0.3,
                y2=0.7,
                modification_date=datetime(2021, 7, 15, tzinfo=timezone.utc),
            ),
            labels=[
                ScoredLabel(
                    label_id=fxt_segmentation_labels[0].id_,
                    is_empty=fxt_segmentation_labels[0].is_empty,
                    probability=1.0,
                )
            ],
            id_="92497df6-f45a-11eb-9a03-0242ac130003",
        )
        segmentation_annotation_2 = Annotation(
            shape=Rectangle(
                x1=0.6,
                x2=0.9,
                y1=0.3,
                y2=0.7,
                modification_date=datetime(2021, 7, 15, tzinfo=timezone.utc),
            ),
            labels=[
                ScoredLabel(
                    label_id=fxt_segmentation_labels[1].id_,
                    is_empty=fxt_segmentation_labels[1].is_empty,
                    probability=1.0,
                )
            ],
            id_="92497df6-f45a-11eb-9a03-0242ac130003",
        )
        _, dataset = fxt_single_crate_image_dataset_for_project(
            project=fxt_detection_segmentation_chain_project,
            annotations=[
                detection_annotation_1,
                detection_annotation_2,
                segmentation_annotation_1,
                segmentation_annotation_2,
            ],
        )
        for item in dataset:
            item.subset = Subset.TRAINING

        task_environment = TaskEnvironment(
            model_template=fxt_model_template_detection,
            model=NullModel(),
            hyper_parameters=ConfigurableParameters(header="Empty parameters"),
            label_schema=label_schema,
        )

        crop_task = CropTask(task_environment=task_environment)

        cropped_dataset = crop_task.infer(dataset=dataset)

        rois = [item.roi for item in cropped_dataset]

        assert len(cropped_dataset) == 2
        assert all(item.subset == Subset.TRAINING for item in cropped_dataset)
        assert cropped_dataset.purpose == dataset.purpose
        assert detection_annotation_1 in rois
        assert detection_annotation_2 in rois

        cropped_dataset_2 = crop_task.infer(dataset=dataset, subset=Subset.UNASSIGNED)
        assert all(item.subset == Subset.UNASSIGNED for item in cropped_dataset_2)
