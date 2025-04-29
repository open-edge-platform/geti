# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy
from itertools import chain
from unittest.mock import patch

import pytest

from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroupType
from sc_sdk.entities.project import Project
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, LabelRepo
from sc_sdk.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from sc_sdk.utils.project_builder import ProjectBuilder
from tests.tools.custom_project_parser import CustomTestProjectParser


@pytest.mark.ScSdkComponent
class TestProjectBuilder:
    @pytest.mark.parametrize(
        "domain, default_name",
        [
            (Domain.ANOMALY_DETECTION, "default - anomaly_detection"),
            (Domain.ANOMALY_SEGMENTATION, "default - anomaly_segmentation"),
            (Domain.ANOMALY_CLASSIFICATION, "default - anomaly_classification"),
        ],
    )
    def test_build_anomaly_labels(
        self,
        domain,
        default_name,
    ):
        label_groups, labels = ProjectBuilder._build_anomaly_labels(domain=domain, task_label_by_group_name={})
        assert len(labels) == 2
        assert len(label_groups) == 1
        assert label_groups[0].name == default_name

    @pytest.mark.parametrize(
        "domain, empty_label_name, label_names_by_group_name, child_name_to_parent_name",
        [
            (Domain.DETECTION, "No object", {}, {}),
            (Domain.SEGMENTATION, "Empty", {}, {}),
            (Domain.INSTANCE_SEGMENTATION, "Empty", {}, {}),
            (Domain.ROTATED_DETECTION, "No object", {}, {}),
            (Domain.CLASSIFICATION, None, {"grpA": ["lab1", "lab2"]}, {}),
            (
                Domain.CLASSIFICATION,
                "No class",
                {"grp1": ["lab1"], "grp2": ["lab2"], "grp1.1": ["lab1.1", "lab1.2"]},
                {"lab1.1": "lab1", "lab1.2": "lab1"},
            ),
        ],
        ids=[
            "detection",
            "semantic segmentation",
            "instance segmentation",
            "rotated detection",
            "multiclass classification",
            "multilabel hierarchical classification",
        ],
    )
    def test_build_groups_and_empty_labels(
        self,
        domain,
        empty_label_name,
        label_names_by_group_name,
        child_name_to_parent_name,
        fxt_ote_id,
    ) -> None:
        task_labels_by_group_name = {
            grp_name: [Label(name=lbl_name, domain=domain, id_=fxt_ote_id(hash(lbl_name))) for lbl_name in label_names]
            for grp_name, label_names in label_names_by_group_name.items()
        }
        custom_labels = list(chain.from_iterable(task_labels_by_group_name.values()))
        child_to_parent_id = {
            next(lbl for lbl in custom_labels if lbl.name == child_name): parent_name
            for child_name, parent_name in child_name_to_parent_name.items()
        }

        label_groups, labels = ProjectBuilder._build_groups_and_empty_labels(
            domain=domain,
            task_labels_by_group_name=task_labels_by_group_name,
            child_to_parent_id=child_to_parent_id,
        )

        if empty_label_name is not None:  # empty label necessary
            assert len(labels) == len(custom_labels) + 1
            assert len(label_groups) == len(task_labels_by_group_name) + 1
            assert any(grp.name == empty_label_name for grp in label_groups)
        else:  # empty label not necessary
            assert len(labels) == len(custom_labels)
            assert len(label_groups) == len(task_labels_by_group_name)

    def test_detection_label_schema_from_pipeline(
        self,
        fxt_detection_classification_project_data,
    ):
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("detection"),
                ModelTemplateList().get_by_id("crop"),
                ModelTemplateList().get_by_id("classification"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_detection_classification_project_data,
            )
        detection_label_group = label_schema.get_label_group_by_name("Default Detection")
        classification_label_group = label_schema.get_label_group_by_name("Default Classification")
        empty_detection_label_group = label_schema.get_label_group_by_name("No object")

        assert classification_label_group is not None
        assert detection_label_group is not None
        assert empty_detection_label_group is not None
        classification_labels = classification_label_group.labels
        detection_label = detection_label_group.labels[0]
        for label in classification_labels:
            assert label_schema.get_parent(label) == detection_label
        assert set(label_schema.get_children(detection_label)) == set(classification_labels)
        assert len(empty_detection_label_group.labels) == 1

    def test_anomaly_label_schema_from_pipeline(
        self,
        fxt_anomaly_classification_project_data,
    ):
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("anomaly_classification"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_anomaly_classification_project_data,
            )

        anomaly_label_group = label_schema.get_label_group_by_name("default - anomaly_classification")

        assert anomaly_label_group is not None
        label_names = {label.name for label in anomaly_label_group.labels}
        assert label_names == {"Anomalous", "Normal"}
        labels_are_anomalous = {label.is_anomalous for label in anomaly_label_group.labels}
        assert labels_are_anomalous == {True, False}

    def test_label_schema_with_hierarchy_task_chain_from_pipeline(
        self,
        fxt_label_hierarchy_task_chain_project_data,
    ):
        """
        <b>Description:</b>
        This test creates a LabelSchema with a hierarchical structure from an input REST
        view of a pipeline.

        <b>Input data:</b>
        A pipeline dictionary that contains two trainable tasks: a segmentation task and
        a classification task. The segmentation task has labels 'cat' and 'dog', and the
        classification task further classifies those in big and small cats/dogs.

        <b>Expected results:</b>
        Test passes if the function label_schema_from_pipeline properly creates a
        hierarchical label schema from pipeline data.

        <b>Steps</b>
        1. Input the pipeline with hierarchical label data to the function label_schema_from_pipeline
        2. Add a finalizer that deletes all data that is written to the repo
        3. Assert that the expected label groups are created (including empty label groups
        which are added without being in the pipeline data)
        4. Assert that the labels have the proper hierarchy
        """
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("detection"),
                ModelTemplateList().get_by_id("crop"),
                ModelTemplateList().get_by_id("classification"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_label_hierarchy_task_chain_project_data,
            )

        expected_group_names = {
            "Default detection",
            "No object",
            "Dog",
            "Cat",
        }
        result_groups = label_schema.get_groups(include_empty=True)
        assert {group.name for group in result_groups} == expected_group_names

        detection_group = [g for g in result_groups if g.name == "Default detection"][0]
        detection_dog_label = [label for label in detection_group.labels if label.name == "dog"][0]
        detection_cat_label = [label for label in detection_group.labels if label.name == "cat"][0]
        classification_group_dog = [g for g in result_groups if g.name == "Dog"][0]
        classification_group_cat = [g for g in result_groups if g.name == "Cat"][0]
        for label in classification_group_dog.labels:
            assert label_schema.get_parent(label) == detection_dog_label
        for label in classification_group_cat.labels:
            assert label_schema.get_parent(label) == detection_cat_label

    def test_label_schema_with_hierarchy_from_pipeline(
        self,
        fxt_hierarchy_classification_project_data_2,
    ):
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("classification"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_hierarchy_classification_project_data_2,
            )

        expected_group_names = {
            "Group 1",
            "Group 1.X",
            "Group 1.1.X",
            "Group 2",
            "Group 2.X",
            "No class",
        }
        groups = label_schema.get_groups(include_empty=True)
        assert {group.name for group in groups} == expected_group_names

        group_1_labels = [g.labels for g in groups if g.name == "Group 1"][0]
        group_1_parent = None

        group_1x_labels = [g.labels for g in groups if g.name == "Group 1.X"][0]
        group_1x_parent = [label for label in group_1_labels if label.name == "1"][0]

        group_11x_labels = [g.labels for g in groups if g.name == "Group 1.1.X"][0]
        group_11x_parent = [label for label in group_1x_labels if label.name == "1.1"][0]

        group_2_labels = [g.labels for g in groups if g.name == "Group 2"][0]
        group_2_parent = None

        group_2x_labels = [g.labels for g in groups if g.name == "Group 2.X"][0]
        group_2x_parent = [label for label in group_2_labels if label.name == "2"][0]

        for label in group_1_labels:
            assert label_schema.get_parent(label) == group_1_parent
        for label in group_1x_labels:
            assert label_schema.get_parent(label) == group_1x_parent
        for label in group_11x_labels:
            assert label_schema.get_parent(label) == group_11x_parent
        for label in group_2_labels:
            assert label_schema.get_parent(label) == group_2_parent
        for label in group_2x_labels:
            assert label_schema.get_parent(label) == group_2x_parent

    def test_label_schema_for_binary_pipeline(
        self,
        fxt_binary_classification_project_data,
    ):
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("classification"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_binary_classification_project_data,
            )

        label_groups = label_schema.get_groups(include_empty=True)
        labels = label_schema.get_labels(include_empty=True)
        assert len(label_groups) == 1
        assert len(labels) == len(fxt_binary_classification_project_data["tasks_dict"]["Classification task"]["labels"])

    def test_label_schema_for_multiclass_pipeline(
        self,
        fxt_multiclass_classification_project_data,
    ):
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("classification"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_multiclass_classification_project_data,
            )
        label_groups = label_schema.get_groups(include_empty=True)
        labels = label_schema.get_labels(include_empty=True)
        assert len(label_groups) == 2
        assert len(labels) == len(
            fxt_multiclass_classification_project_data["tasks_dict"]["Classification task"]["labels"]
        )
        assert not [label for label in labels if label.is_empty]
        assert not [label_group for label_group in label_groups if label_group.group_type == LabelGroupType.EMPTY_LABEL]

    def test_label_schema_for_multilabel_pipeline(
        self,
        fxt_multilabel_classification_project_data,
    ):
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("classification"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_multilabel_classification_project_data,
            )

        label_groups = label_schema.get_groups(include_empty=True)
        labels = label_schema.get_labels(include_empty=True)
        assert len(label_groups) == 3
        assert len(labels) == len(
            fxt_multilabel_classification_project_data["tasks_dict"]["Classification task"]["labels"]
        )

    def test_label_schema_for_segmentation_pipeline(
        self,
        fxt_segmentation_project_data,
    ):
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("segmentation"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti", parser_class=CustomTestProjectParser, parser_kwargs=fxt_segmentation_project_data
            )

        label_groups = label_schema.get_groups(include_empty=True)
        labels = label_schema.get_labels(include_empty=True)
        assert len(label_groups) == 2
        assert len(labels) == len(fxt_segmentation_project_data["tasks_dict"]["Segmentation task"]["labels"]) + 1
        assert len([label for label in labels if label.is_empty]) == 1
        assert (
            len([label_group for label_group in label_groups if label_group.group_type == LabelGroupType.EMPTY_LABEL])
            == 1
        )

    def test_detection_to_segmentation_labels_from_pipeline(
        self,
        fxt_detection_to_segmentation_project_data,
    ):
        """
        <b>Description:</b>
        This test creates a LabelSchema with a hierarchical structure from an input REST
        view of a pipeline with a detection task and a segmentation task.

        <b>Input data:</b>
        A pipeline dictionary that contains two trainable tasks: a detection task and
        a segmentation task.

        <b>Expected results:</b>
        Test passes if the function label_schema_from_pipeline properly creates a label schema.
        There must be no hierarchy in the label schema since no hierarchy is specified in the pipeline and it
        should not be automatically created for local->local task chains.

        <b>Steps</b>
        1. Input the pipeline with label data to the function label_schema_from_pipeline
        2. Add a finalizer that deletes all data that is written to the repo
        3. Assert that the expected label groups are created (including empty label groups
        which are added without being in the pipeline data)
        4. Assert that the labels have no hierarchy
        """
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id("detection"),
                ModelTemplateList().get_by_id("crop"),
                ModelTemplateList().get_by_id("segmentation"),
            ],
        ):
            project, label_schema, task_schema = ProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=fxt_detection_to_segmentation_project_data,
            )
        expected_group_names = {
            "Default Detection",
            "No object",
            "Default Segmentation",
            "Empty",
        }
        result_groups = label_schema.get_groups(include_empty=True)
        assert {group.name for group in result_groups} == expected_group_names

        for label in label_schema.get_labels(include_empty=True):
            assert label_schema.get_parent(label) is None

    def test_remove_label_shape_delete(self, fxt_detection_project, fxt_label, fxt_dataset_storage):
        """
        Tests that when removing the last label from an annotation, the entire annotation is removed from the scene.
        """
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            annotations=[Annotation(shape=Rectangle.generate_full_box(), labels=[fxt_label])],
        )
        expected_annotation_scene = copy.deepcopy(annotation_scene)
        expected_annotation_scene.annotations = []
        with (
            patch.object(LabelRepo, "save", return_value=None),
            patch.object(Project, "get_dataset_storages", return_value=[fxt_dataset_storage]),
            patch.object(AnnotationSceneRepo, "get_all_by_kind_and_labels", return_value=[annotation_scene]),
            patch.object(AnnotationSceneStateHelper, "compute_annotation_scene_state", return_value=None),
            patch.object(AnnotationSceneStateRepo, "save", return_value=None),
            patch.object(AnnotationSceneRepo, "save", return_value=None) as fxt_save,
        ):
            ProjectBuilder._remove_label_from_project(fxt_detection_project, fxt_label)

        fxt_save.assert_called_with(expected_annotation_scene)
