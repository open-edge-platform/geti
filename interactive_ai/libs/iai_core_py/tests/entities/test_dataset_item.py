# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime
from copy import deepcopy

import numpy as np

from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.color import Color
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.image import Image
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.metadata import MetadataItem
from iai_core.entities.model import Model, ModelConfiguration
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Point, Polygon, Rectangle
from iai_core.entities.subset import Subset
from iai_core.entities.tensor import Tensor

from geti_types import ID, NullMediaIdentifier


class DatasetItemParameters:
    @staticmethod
    def generate_random_image() -> Image:
        image = Image(
            id=ID(np.random.randint(10000, size=1)[0]),
            name="test_image",
            uploader_id="uploader",
            width=16,
            height=10,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        return image

    @staticmethod
    def labels() -> list[Label]:
        creation_date = datetime.datetime(year=2021, month=12, day=9)
        detection_label = Label(
            name="Label for Detection",
            domain=Domain.DETECTION,
            color=Color(red=100, green=200, blue=150),
            creation_date=creation_date,
            id_=ID("detection_label"),
        )
        segmentation_label = Label(
            name="Label for Segmentation",
            domain=Domain.DETECTION,
            color=Color(red=50, green=80, blue=200),
            creation_date=creation_date,
            is_empty=True,
            id_=ID("segmentation_label"),
        )
        return [detection_label, segmentation_label]

    def annotations(self) -> list[Annotation]:
        labels = self.labels()
        rectangle = Rectangle(x1=0.2, y1=0.2, x2=0.6, y2=0.7)
        other_rectangle = Rectangle(x1=0.3, y1=0.2, x2=0.9, y2=0.9)
        detection_annotation = Annotation(
            shape=rectangle,
            labels=[ScoredLabel(label_id=labels[0].id_, is_empty=labels[0].is_empty)],
            id_=ID("detection_annotation_1"),
        )
        segmentation_annotation = Annotation(
            shape=other_rectangle,
            labels=[ScoredLabel(label_id=labels[1].id_, is_empty=labels[1].is_empty)],
            id_=ID("segmentation_annotation_1"),
        )
        return [detection_annotation, segmentation_annotation]

    @staticmethod
    def roi_labels() -> list[Label]:
        creation_date = datetime.datetime(year=2021, month=12, day=9)
        roi_label = Label(
            name="ROI label",
            domain=Domain.DETECTION,
            color=Color(red=40, green=180, blue=80),
            creation_date=creation_date,
            id_=ID("roi_label_1"),
        )
        other_roi_label = Label(
            name="Second ROI label",
            domain=Domain.SEGMENTATION,
            color=Color(red=80, green=90, blue=70),
            creation_date=creation_date,
            is_empty=True,
            id_=ID("roi_label_2"),
        )
        return [roi_label, other_roi_label]

    def roi_scored_labels(self) -> list[ScoredLabel]:
        roi_labels = self.roi_labels()
        return [
            ScoredLabel(label_id=roi_labels[0].id_, is_empty=roi_labels[0].is_empty),
            ScoredLabel(label_id=roi_labels[1].id_, is_empty=roi_labels[1].is_empty),
        ]

    def roi(self):
        roi = Annotation(
            shape=Rectangle(
                x1=0.1,
                y1=0.1,
                x2=0.9,
                y2=0.9,
                modification_date=datetime.datetime(year=2021, month=12, day=9),
            ),
            labels=self.roi_scored_labels(),
            id_=ID("roi_annotation"),
        )
        return roi

    @staticmethod
    def metadata() -> list[MetadataItem]:
        data = Tensor(
            name="test_metadata",
            numpy=np.random.uniform(low=0.0, high=255.0, size=(10, 15, 3)),
        )
        other_data = Tensor(
            name="other_metadata",
            numpy=np.random.uniform(low=0.0, high=255.0, size=(10, 15, 3)),
        )
        return [
            MetadataItem(id=ID(), dataset_item_id=ID(), data=data),
            MetadataItem(id=ID(), dataset_item_id=ID(), data=other_data),
        ]

    def annotations_entity(self) -> AnnotationScene:
        return AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            id_=ID("annotation_entity_1"),
            creation_date=datetime.datetime(year=2021, month=12, day=19),
            annotations=self.annotations(),
        )

    def default_values_dataset_item(self) -> DatasetItem:
        return DatasetItem(id_=ID(), media=self.generate_random_image(), annotation_scene=self.annotations_entity())

    def dataset_item(self) -> DatasetItem:
        return DatasetItem(
            id_=ID("test"),
            media=self.generate_random_image(),
            annotation_scene=self.annotations_entity(),
            roi=self.roi(),
            metadata=self.metadata(),
            subset=Subset.TESTING,
            ignored_label_ids={self.labels()[1].id_},
        )


class TestDatasetItem:
    def test_get_next_task_rois(self, fxt_classification_labels, fxt_detection_labels, fxt_empty_image) -> None:
        # Arrange
        shapes = [Rectangle(x1=(0 + c) / 10, x2=(2 + c) / 10, y1=(0 + c) / 10, y2=(2 + c) / 10) for c in range(6)]
        scored_labels_class = [
            ScoredLabel(label_id=label.id_, is_empty=label.is_empty) for label in fxt_classification_labels
        ]
        scored_labels_det = [ScoredLabel(label_id=label.id_, is_empty=label.is_empty) for label in fxt_detection_labels]
        empty_label = ScoredLabel(label_id=ID("empty_label"), is_empty=True)

        annotation_class_1 = Annotation(shape=shapes[0], labels=scored_labels_class[:1])
        annotation_class_2 = Annotation(shape=shapes[1], labels=scored_labels_class[:2])
        annotation_mixed_3 = Annotation(
            shape=shapes[2],
            labels=[
                scored_labels_class[1],
                scored_labels_class[2],
                scored_labels_det[0],
            ],
        )
        annotation_mixed_4 = Annotation(shape=shapes[3], labels=[scored_labels_class[2], scored_labels_det[0]])
        annotation_det_5 = Annotation(shape=shapes[4], labels=scored_labels_det)
        annotation_empty_6 = Annotation(shape=shapes[5], labels=[empty_label])

        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=NullMediaIdentifier(),
            media_height=100,
            media_width=100,
            id_=ID(),
            annotations=[
                annotation_class_1,
                annotation_class_2,
                annotation_mixed_3,
                annotation_mixed_4,
                annotation_det_5,
                annotation_empty_6,
            ],
        )

        # Ignore third classification label
        dataset_item = DatasetItem(
            id_=ID(),
            media=fxt_empty_image,
            annotation_scene=annotation_scene,
            ignored_label_ids=[fxt_classification_labels[2].id_],
        )

        # Act
        # Only second and third classification label belong to previous task
        result = dataset_item.get_rois_containing_labels(labels=fxt_classification_labels[1:])

        # Assert
        assert result == [annotation_class_2, annotation_mixed_3]

    @staticmethod
    def compare_denormalized_annotations(actual_annotations, expected_annotations) -> None:
        assert len(actual_annotations) == len(expected_annotations)
        for index in range(len(expected_annotations)):
            actual_annotation = actual_annotations[index]
            expected_annotation = expected_annotations[index]
            # Redefining id and modification_date required because of new Annotation objects created after shape
            # denormalize
            actual_annotation.id_ = expected_annotation.id_
            actual_annotation.shape.modification_date = expected_annotation.shape.modification_date
            assert actual_annotation == expected_annotation

    @staticmethod
    def labels_to_add() -> list[Label]:
        label_to_add = Label(
            name="Label which will be added",
            domain=Domain.DETECTION,
            color=Color(red=60, green=120, blue=70),
            creation_date=datetime.datetime(year=2021, month=12, day=12),
            id_=ID("label_to_add_1"),
        )
        other_label_to_add = Label(
            name="Other label to add",
            domain=Domain.SEGMENTATION,
            color=Color(red=80, green=70, blue=100),
            creation_date=datetime.datetime(year=2021, month=12, day=11),
            is_empty=True,
            id_=ID("label_to_add_2"),
        )
        return [label_to_add, other_label_to_add]

    def annotations_to_add(self) -> list[Annotation]:
        labels_to_add = self.labels_to_add()
        annotation_to_add = Annotation(
            shape=Rectangle(x1=0.1, y1=0.1, x2=0.7, y2=0.8),
            labels=[ScoredLabel(label_id=labels_to_add[0].id_, is_empty=labels_to_add[0].is_empty)],
            id_=ID("added_annotation_1"),
        )
        other_annotation_to_add = Annotation(
            shape=Rectangle(x1=0.2, y1=0.3, x2=0.8, y2=0.9),
            labels=[ScoredLabel(label_id=labels_to_add[1].id_, is_empty=labels_to_add[1].is_empty)],
            id_=ID("added_annotation_2"),
        )
        return [annotation_to_add, other_annotation_to_add]

    @staticmethod
    def metadata_item_with_model() -> MetadataItem:
        data = Tensor(
            name="appended_metadata_with_model",
            numpy=np.random.randint(low=0, high=255, size=(10, 15, 3)),
        )
        configuration = ModelConfiguration(
            configurable_parameters=ConfigurableParameters(header="Test Header"),
            label_schema=LabelSchema(id_=ID("label_schema_id")),
        )
        model = Model(
            project=None,  # type: ignore[arg-type]
            model_storage=None,  # type: ignore[arg-type]
            train_dataset=Dataset(id=ID()),
            configuration=configuration,
            id_=ID("model"),
        )
        metadata_item_with_model = MetadataItem(id=ID(), dataset_item_id=ID(), data=data, model=model)
        return metadata_item_with_model

    @staticmethod
    def check_roi_equal_annotation(dataset_item: DatasetItem, expected_labels: list, include_empty=False) -> None:
        roi_annotation_in_scene = None
        for annotation in dataset_item.annotation_scene.annotations:
            if annotation == dataset_item.roi:
                assert annotation.get_labels(include_empty=include_empty) == expected_labels
                roi_annotation_in_scene = annotation
                break
        assert roi_annotation_in_scene

    def test_dataset_item_initialization(self):
        """
        <b>Description:</b>
        Check DatasetItem class object initialization

        <b>Input data:</b>
        DatasetItem class objects with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if attributes of DatasetItem class object are equal to expected

        <b>Steps</b>
        1. Check attributes of DatasetItem object initialized with default optional parameters
        2. Check attributes of DatasetItem object initialized with specified optional parameters
        """
        media = DatasetItemParameters.generate_random_image()
        annotations_scene = DatasetItemParameters().annotations_entity()
        # Checking attributes of DatasetItem object initialized with default optional parameters
        default_values_dataset_item = DatasetItem(id_=ID(), media=media, annotation_scene=annotations_scene)
        assert default_values_dataset_item.media == media
        assert default_values_dataset_item.annotation_scene == annotations_scene
        assert not default_values_dataset_item.get_metadata()
        assert default_values_dataset_item.subset == Subset.NONE
        assert default_values_dataset_item.ignored_label_ids == set()
        # Checking attributes of DatasetItem object initialized with specified optional parameters
        roi = DatasetItemParameters().roi()
        metadata = DatasetItemParameters.metadata()
        subset = Subset.TESTING
        ignored_label_ids = {label.id_ for label in DatasetItemParameters().labels()}
        specified_values_dataset_item = DatasetItem(
            id_=ID(),
            media=media,
            annotation_scene=annotations_scene,
            roi=roi,
            metadata=metadata,
            subset=subset,
            ignored_label_ids=ignored_label_ids,
        )
        assert specified_values_dataset_item.media == media
        assert specified_values_dataset_item.annotation_scene == annotations_scene
        assert specified_values_dataset_item.roi == roi
        assert specified_values_dataset_item.get_metadata() == metadata
        assert specified_values_dataset_item.subset == subset
        assert specified_values_dataset_item.ignored_label_ids == ignored_label_ids

    def test_dataset_item_roi(self):
        """
        <b>Description:</b>
        Check DatasetItem class "roi" property

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if value returned by "roi" property is equal to expected

        <b>Steps</b>
        1. Check value returned by "roi" property for DatasetItem with specified "roi" parameter
        2. Check value returned by "roi" property for DatasetItem with not specified "roi" parameter
        3. Check value returned by "roi" property for DatasetItem with not specified "roi" parameter but one
        of annotation objects in annotation_scene is equal to full Rectangle
        """
        media = DatasetItemParameters.generate_random_image()
        annotations = DatasetItemParameters().annotations()
        annotation_scene = DatasetItemParameters().annotations_entity()
        roi = DatasetItemParameters().roi()
        metadata = DatasetItemParameters.metadata()
        # Checking "roi" property for DatasetItem with specified "roi" parameter
        specified_roi_dataset_item = DatasetItemParameters().dataset_item()
        assert specified_roi_dataset_item.roi == roi
        # Checking that "roi" property is equal to full_box for DatasetItem with not specified "roi" parameter
        non_specified_roi_dataset_item = DatasetItem(ID(), media, annotation_scene, metadata=metadata)
        default_roi = non_specified_roi_dataset_item.roi.shape
        assert isinstance(default_roi, Rectangle)
        assert Rectangle.is_full_box(default_roi)
        # Checking that "roi" property will be equal to full_box for DatasetItem with not specified "roi" but one
        # of Annotation objects in annotation_scene is equal to full Rectangle
        full_box_label = Label(ID("full_box_label"), "Full-box label", Domain.DETECTION)
        full_box_annotation = Annotation(
            Rectangle.generate_full_box(), [ScoredLabel(label_id=full_box_label.id_, is_empty=full_box_label.is_empty)]
        )
        annotations.append(full_box_annotation)
        annotation_scene.annotations.append(full_box_annotation)
        full_box_label_dataset_item = DatasetItem(ID(), media, annotation_scene, metadata=metadata)
        assert full_box_label_dataset_item.roi is full_box_annotation

    def test_dataset_item_width(self):
        """
        <b>Description:</b>
        Check DatasetItem class "width" property

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if value returned by "width" property is equal to expected

        <b>Steps</b>
        1. Check value returned by "width" property for DatasetItem with "roi" attribute is "None"
        2. Check value returned by "width" property for DatasetItem with specified "roi" attribute
        """
        # Checking value returned by "width" property for DatasetItem with "roi" attribute is "None"
        none_roi_dataset_item = DatasetItemParameters().default_values_dataset_item()
        assert none_roi_dataset_item.width == 16
        # Checking value returned by "width" property for DatasetItem with specified "roi" attribute
        roi_specified_dataset_item = DatasetItemParameters().dataset_item()
        assert roi_specified_dataset_item.width == 12

    def test_dataset_item_height(self):
        """
        <b>Description:</b>
        Check DatasetItem class "height" property

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if value returned by "height" property is equal to expected

        <b>Steps</b>
        1. Check value returned by "height" property for DatasetItem with "roi" attribute is "None"
        2. Check value returned by "height" property for DatasetItem with specified "roi" attribute
        """
        # Checking value returned by "width" property for DatasetItem with None "roi" attribute
        none_roi_dataset_item = DatasetItemParameters().default_values_dataset_item()
        assert none_roi_dataset_item.height == 10
        # Checking value returned by "width" property for DatasetItem with specified "roi" attribute
        roi_specified_dataset_item = DatasetItemParameters().dataset_item()
        assert roi_specified_dataset_item.height == 8

    def test_dataset_item_get_annotations(self):
        """
        <b>Description:</b>
        Check DatasetItem class "get_annotations" method

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if list returned by "get_annotations" method is equal to expected

        <b>Steps</b>
        1. Check that get_annotations returns all annotations in the dataset item if the ROI is a full box
        2. Check that after adding the parameter "labels", only the annotations with that label are returned
        3. Check that for a ROI that includes only one of the annotations, only that annotation is returned
        """
        # Check that get_annotations returns all items if the ROI is a full box.
        full_box_roi_dataset_item = DatasetItemParameters().default_values_dataset_item()
        full_box_annotations = list(full_box_roi_dataset_item.annotation_scene.annotations)
        result_annotations = full_box_roi_dataset_item.get_annotations(include_empty=True)
        expected_annotations = full_box_annotations
        self.compare_denormalized_annotations(result_annotations, expected_annotations)

        # Check that get_annotations returns only the items with the right label if the "labels" param is used
        first_annotation = full_box_roi_dataset_item.annotation_scene.annotations[0]
        first_annotation_label = first_annotation.get_labels()[0].label_id
        result_annotations = full_box_roi_dataset_item.get_annotations(
            label_ids=[first_annotation_label], include_empty=True
        )
        expected_annotations = [first_annotation]
        self.compare_denormalized_annotations(result_annotations, expected_annotations)

        # Check that get_annotations only returns the annotations whose center falls within the ROI
        partial_box_dataset_item = deepcopy(full_box_roi_dataset_item)
        partial_box_dataset_item.roi = Annotation(shape=Rectangle(x1=0.0, y1=0.0, x2=0.4, y2=0.5), labels=[])
        expected_annotation = deepcopy(first_annotation)
        expected_annotation.shape = expected_annotation.shape.denormalize_wrt_roi_shape(
            roi_shape=partial_box_dataset_item.roi.shape
        )
        result_annotations = partial_box_dataset_item.get_annotations(include_empty=True)
        self.compare_denormalized_annotations(result_annotations, [expected_annotation])

        # Check if ignored labels are properly removed
        ignore_labels_dataset_item = DatasetItemParameters().default_values_dataset_item()
        ignore_labels_dataset_item.ignored_label_ids = ignore_labels_dataset_item.get_shapes_label_ids(
            include_empty=True, include_ignored=True
        )
        assert ignore_labels_dataset_item.get_annotations(include_empty=True) == []

    def test_dataset_item_append_annotations(self):
        """
        <b>Description:</b>
        Check DatasetItem class "append_annotations" method

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if annotations list returned after "append_annotations" method is equal to expected

        <b>Steps</b>
        1. Check annotations list returned after "append_annotations" method with specified non-included annotations
        2. Check annotations list returned after "append_annotations" method with incorrect shape annotation
        """
        # Checking annotations list returned after "append_annotations" method with specified non-included annotations
        dataset_item = DatasetItemParameters().default_values_dataset_item()
        full_box_annotations = list(dataset_item.annotation_scene.annotations)
        annotations_to_add = self.annotations_to_add()
        normalized_annotations = []
        for annotation in annotations_to_add:
            normalized_annotations.append(
                Annotation(
                    shape=annotation.shape.normalize_wrt_roi_shape(dataset_item.roi.shape),
                    labels=annotation.get_labels(),
                )
            )
        dataset_item.append_annotations(annotations_to_add)
        # Random id is generated for normalized annotations
        normalized_annotations[0].id_ = dataset_item.annotation_scene.annotations[2].id_
        normalized_annotations[1].id_ = dataset_item.annotation_scene.annotations[3].id_
        assert dataset_item.annotation_scene.annotations == full_box_annotations + normalized_annotations
        # Checking annotations list returned after "append_annotations" method with incorrect shape annotation
        incorrect_shape_label = Label(
            name="Label for incorrect shape",
            domain=Domain.CLASSIFICATION,
            color=Color(red=80, green=70, blue=155),
            id_=ID("incorrect_shape_label"),
        )
        incorrect_polygon = Polygon([Point(x=0.01, y=0.1), Point(x=0.35, y=0.1), Point(x=0.35, y=-0.1)])
        incorrect_shape_annotation = Annotation(
            shape=incorrect_polygon,
            labels=[ScoredLabel(label_id=incorrect_shape_label.id_, is_empty=incorrect_shape_label.is_empty)],
            id_=ID("incorrect_shape_annotation"),
        )
        dataset_item.append_annotations([incorrect_shape_annotation])
        assert dataset_item.annotation_scene.annotations == full_box_annotations + normalized_annotations

    def test_dataset_item_get_roi_labels(self):
        """
        <b>Description:</b>
        Check DatasetItem class "get_roi_label_ids" method

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if annotations list returned by "get_roi_label_ids" method is equal to expected

        <b>Steps</b>
        1. Check annotations list returned by "get_roi_label_ids" for non-specified "labels" parameter
        2. Check annotations list returned by "get_roi_label_ids" for specified "labels" parameter
        3. Check annotations list returned by "get_roi_label_ids" if dataset item ignores a label
        """
        dataset_item = DatasetItemParameters().dataset_item()
        roi_labels = DatasetItemParameters.roi_labels()
        # Checking annotations list returned by "get_roi_label_ids" method with non-specified labels parameter
        # Scenario for "include_empty" is "False"
        assert dataset_item.get_roi_label_ids() == {roi_labels[0].id_}
        # Scenario for "include_empty" is "True"
        assert dataset_item.get_roi_label_ids(include_empty=True) == {label.id_ for label in roi_labels}
        # Checking annotations list returned by "get_roi_label_ids" method with specified labels parameter
        empty_roi_label = roi_labels[1]
        # Scenario for "include_empty" is "False"
        assert dataset_item.get_roi_label_ids(label_ids=[empty_roi_label.id_]) == set()
        # Scenario for "include_empty" is "True"
        assert dataset_item.get_roi_label_ids(label_ids=[empty_roi_label.id_], include_empty=True) == {
            empty_roi_label.id_
        }
        # Scenario for ignored labels
        dataset_item.ignored_label_ids = {empty_roi_label.id_}
        assert dataset_item.get_roi_label_ids(label_ids=[empty_roi_label.id_], include_empty=True) == set()

    def test_dataset_item_get_shapes_labels(self):
        """
        <b>Description:</b>
        Check DatasetItem class "get_shapes_labels" method

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if labels list returned by "get_shapes_labels" method is equal to expected

        <b>Steps</b>
        1. Check labels list returned by "get_shapes_labels" for non-specified "labels" parameter
        2. Check labels list returned by "get_shapes_labels" for specified "labels" parameter
        3. Check labels list returned by "get_shapes_labels" if dataset_item ignores labels
        """
        dataset_item = DatasetItemParameters().default_values_dataset_item()
        labels = DatasetItemParameters.labels()
        detection_label = labels[0]
        segmentation_label = labels[1]
        # Checking labels list returned by "get_shapes_labels" method with non-specified "labels" parameter
        # Scenario for "include_empty" is "False"
        assert dataset_item.get_shapes_label_ids() == {detection_label.id_}
        # Scenario for "include_empty" is "True"
        shapes_labels_actual = dataset_item.get_shapes_label_ids(include_empty=True)
        assert len(shapes_labels_actual) == 2
        assert isinstance(shapes_labels_actual, set)
        assert detection_label.id_ in shapes_labels_actual
        assert segmentation_label.id_ in shapes_labels_actual
        # Checking labels list returned by "get_shapes_labels" method with specified "labels" parameter
        # Scenario for "include_empty" is "False"
        non_included_label = Label(ID("non_included_label"), "Non-included label", Domain.CLASSIFICATION)
        list_labels = [segmentation_label.id_, non_included_label.id_]
        assert dataset_item.get_shapes_label_ids(label_ids=list_labels) == set()
        # Scenario for "include_empty" is "True", expected that non_included label will not be shown
        assert dataset_item.get_shapes_label_ids(label_ids=list_labels, include_empty=True) == {segmentation_label.id_}
        # Check ignore labels functionality
        dataset_item.ignored_label_ids = {detection_label.id_}
        assert dataset_item.get_shapes_label_ids(include_empty=True, include_ignored=False) == {segmentation_label.id_}
        assert dataset_item.get_shapes_label_ids(include_empty=False, include_ignored=True) == {detection_label.id_}

    def test_dataset_item_append_labels(self):
        """
        <b>Description:</b>
        Check DatasetItem class "append_labels" method

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if annotations list returned after using "append_labels" method is equal to expected

        <b>Steps</b>
        1. Check annotations list after "append_labels" method for DatasetItem object with ROI-annotation
        specified in annotation_scene.annotations
        2. Check annotations list after "append_labels" method for DatasetItem object with non-specified
        ROI-annotation in annotation_scene.annotations
        """
        annotation_labels = DatasetItemParameters.labels()
        labels_to_add = self.labels_to_add()
        scored_labels_to_add = [
            ScoredLabel(label_id=labels_to_add[0].id_, is_empty=labels_to_add[0].is_empty),
            ScoredLabel(label_id=labels_to_add[1].id_, is_empty=labels_to_add[1].is_empty),
        ]
        media = DatasetItemParameters.generate_random_image()
        roi_labels = DatasetItemParameters.roi_labels()
        roi_scored_labels = DatasetItemParameters().roi_scored_labels()
        roi = DatasetItemParameters().roi()
        equal_roi = DatasetItemParameters().roi()
        annotations = DatasetItemParameters().annotations()
        annotations_with_roi = annotations + [equal_roi]
        annotations_scene = AnnotationScene(annotations=annotations_with_roi, kind=AnnotationSceneKind.ANNOTATION)
        # Scenario for checking "append_labels" method for DatasetItem object with ROI-annotation specified in
        # annotation_scene.annotations object
        roi_label_dataset_item = DatasetItem(ID(), media, annotations_scene, roi)
        roi_label_dataset_item.append_labels(scored_labels_to_add)
        # Check for include_empty is "False"
        expected_labels = {annotation_labels[0].id_, roi_labels[0].id_, labels_to_add[0].id_}
        assert roi_label_dataset_item.annotation_scene.get_label_ids() == expected_labels
        expected_labels = [roi_scored_labels[0], scored_labels_to_add[0]]
        self.check_roi_equal_annotation(roi_label_dataset_item, expected_labels)
        # Check for include_empty is "True"
        expected_labels = annotation_labels + roi_labels + labels_to_add
        assert roi_label_dataset_item.annotation_scene.get_label_ids(True) == {label.id_ for label in expected_labels}
        expected_labels = roi_scored_labels + scored_labels_to_add
        self.check_roi_equal_annotation(roi_label_dataset_item, expected_labels, True)
        # Scenario for checking "append_labels" method for DatasetItem object with non-specified ROI-annotation in
        # annotation_scene.annotations object
        non_roi_dataset_item = DatasetItemParameters().dataset_item()
        non_roi_dataset_item.append_labels(scored_labels_to_add)
        # Check for "include_empty" is "False"
        expected_labels = [annotation_labels[0], roi_labels[0], labels_to_add[0]]
        assert non_roi_dataset_item.annotation_scene.get_label_ids() == {label.id_ for label in expected_labels}
        expected_labels = [roi_scored_labels[0], scored_labels_to_add[0]]
        self.check_roi_equal_annotation(non_roi_dataset_item, expected_labels)
        # Check for "include_empty" is "True"
        expected_labels = annotation_labels + roi_labels + labels_to_add
        assert non_roi_dataset_item.annotation_scene.get_label_ids(True) == {label.id_ for label in expected_labels}
        expected_labels = roi_scored_labels + scored_labels_to_add
        self.check_roi_equal_annotation(non_roi_dataset_item, expected_labels, True)
        # Scenario for "labels" parameter is equal to []
        dataset_item = DatasetItemParameters().dataset_item()
        dataset_item.append_labels([])
        assert dataset_item.annotation_scene.get_label_ids() == {annotation_labels[0].id_}
        assert dataset_item.annotation_scene.get_label_ids(include_empty=True) == {
            label.id_ for label in annotation_labels
        }

    def test_dataset_item_append_metadata_item(self):
        """
        <b>Description:</b>
        Check DatasetItem class "append_metadata_item" method

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if "metadata" attribute after "append_metadata_item" method is equal to expected

        <b>Steps</b>
        1. Check "metadata" attribute after "append_metadata_item" method with non-specified "model" parameter
        2. Check "metadata" attribute after "append_metadata_item" method with specified "model" parameter
        """
        dataset_item = DatasetItemParameters().dataset_item()
        expected_metadata = dataset_item.get_metadata()
        # Checking metadata attribute returned after "append_metadata_item" method with non-specified "model" parameter
        data_to_append = Tensor(
            name="appended_metadata",
            numpy=np.random.uniform(low=0.0, high=255.0, size=(10, 15, 3)),
        )
        dataset_item.append_metadata_item(data=data_to_append)
        metadata = dataset_item.get_metadata()
        expected_metadata.append(
            MetadataItem(
                id=metadata[2].id_,
                dataset_item_id=dataset_item.id_,
                media_identifier=dataset_item.media_identifier,
                data=data_to_append,
            )
        )
        assert metadata == expected_metadata
        # Checking metadata attribute returned after "append_metadata_item" method with specified "model" parameter
        metadata_item_with_model = self.metadata_item_with_model()
        data_to_append = metadata_item_with_model.data
        model_to_append = metadata_item_with_model.model
        dataset_item.append_metadata_item(data_to_append, model_to_append)
        metadata = dataset_item.get_metadata()
        new_metadata_item_with_model = MetadataItem(
            id=metadata[3].id_,
            dataset_item_id=dataset_item.id_,
            media_identifier=dataset_item.media_identifier,
            data=data_to_append,
            model=model_to_append,
        )
        expected_metadata.append(new_metadata_item_with_model)
        assert dataset_item.get_metadata() == expected_metadata

    def test_dataset_item_get_metadata_by_name_and_model(self):
        """
        <b>Description:</b>
        Check DatasetItem class "get_metadata_by_name_and_model" method

        <b>Input data:</b>
        DatasetItem class object with specified "media", "annotation_scene", "roi", "metadata" and "subset"
        parameters

        <b>Expected results:</b>
        Test passes if MetadataItem object returned by "get_metadata_by_name_and_model" is equal to expected

        <b>Steps</b>
        1. Check value returned by "get_metadata_by_name_and_model" method for searching metadata object with "model"
        is "None"
        2. Check value returned by "get_metadata_by_name_and_model" method for searching metadata object with specified
        "model" attribute
        3. Check value returned by "get_metadata_by_name_and_model" method for searching non-existing metadata object
        """
        dataset_item = DatasetItemParameters().dataset_item()
        metadata_item_with_model = self.metadata_item_with_model()
        dataset_model = metadata_item_with_model.model
        dataset_item.append_metadata_item(metadata_item_with_model.data, dataset_model)
        dataset_metadata = dataset_item.get_metadata()
        # Checking "get_metadata_by_name_and_model" method for "model" parameter is "None"
        assert dataset_item.get_metadata_by_name_and_model("test_metadata", None) == [dataset_metadata[0]]
        # Checking "get_metadata_by_name_and_model" method for specified "model" parameter
        assert dataset_item.get_metadata_by_name_and_model("appended_metadata_with_model", dataset_model) == [
            dataset_metadata[2]
        ]
        # Checking "get_metadata_by_name_and_model" method for searching non-existing metadata
        assert dataset_item.get_metadata_by_name_and_model("test_metadata", dataset_model) == []
        assert dataset_item.get_metadata_by_name_and_model("appended_metadata_with_model", None) == []
