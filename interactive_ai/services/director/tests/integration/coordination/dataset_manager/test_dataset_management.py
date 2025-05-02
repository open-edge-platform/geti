# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import time
from random import randint, uniform

from bson import ObjectId
from flaky import flaky
from tests.mock_tasks import register_classification_task
from tests.test_helpers import ID, construct_and_save_train_dataset_for_task, generate_random_annotated_project

from coordination.dataset_manager.dataset_counter import DatasetCounterUseCase
from coordination.dataset_manager.dataset_counter_config import DatasetCounterConfig
from coordination.dataset_manager.dataset_suspender import DatasetSuspender
from coordination.dataset_manager.dataset_update import DatasetUpdateUseCase
from coordination.dataset_manager.missing_annotations_helper import MissingAnnotationsHelper
from entities.dataset_item_labels import DatasetItemLabels
from storage.repos import DatasetItemCountRepo, DatasetItemLabelsRepo

from geti_types import DatasetStorageIdentifier, ImageIdentifier, MediaIdentifierEntity
from iai_core_py.configuration.elements.component_parameters import ComponentParameters, ComponentType
from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core_py.entities.datasets import Dataset, DatasetPurpose
from iai_core_py.entities.image import Image
from iai_core_py.entities.label import Label
from iai_core_py.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core_py.entities.model import Model, ModelConfiguration
from iai_core_py.entities.scored_label import ScoredLabel
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.entities.subset import Subset
from iai_core_py.entities.suspended_scenes import SuspendedAnnotationScenesDescriptor
from iai_core_py.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    ImageRepo,
    ModelRepo,
    SuspendedAnnotationScenesRepo,
)
from iai_core_py.repos.dataset_entity_repo import PipelineDatasetRepo
from iai_core_py.services.model_service import ModelService
from iai_core_py.utils.dataset_helper import DatasetHelper
from iai_core_py.utils.deletion_helpers import DeletionHelpers


class TestDatasetManagement:
    @staticmethod
    def create_randomized_annotations(number_of_annotations, detection_label, classification_label) -> list[Annotation]:
        random_definitions = [
            (
                uniform(0, 0.5),
                uniform(0, 0.5),
                randint(0, len(detection_label) - 1),
                randint(0, len(classification_label) - 1),
            )
            for _ in range(number_of_annotations)
        ]
        randomized_annotations = []
        for x1, y1, i1, i2 in random_definitions:
            shape = Rectangle(x1=x1, y1=y1, x2=x1 + 0.3, y2=y1 + 0.3)
            labels = [
                ScoredLabel(label_id=detection_label[i1].id_, is_empty=detection_label[i1].is_empty, probability=1.0),
                ScoredLabel(
                    label_id=classification_label[i2].id_, is_empty=classification_label[i2].is_empty, probability=1.0
                ),
            ]
            randomized_annotations.append(Annotation(shape=shape, labels=labels))
        return randomized_annotations

    @staticmethod
    def get_subsets_from_dataset(
        dataset: Dataset,
    ) -> dict[MediaIdentifierEntity, dict[ID, Subset]]:
        subsets: dict[MediaIdentifierEntity, dict[ID, Subset]] = {}
        for item in dataset:
            media_id = item.media_identifier
            roi_id = item.roi.id_
            if media_id not in subsets:
                subsets[media_id] = {}
            subsets[media_id][roi_id] = item.subset
        return subsets

    def test_dataset_manager(
        self,
        request,
        fxt_test_dataset_manager_data,
        fxt_dataset,
    ) -> None:
        """
        <b>Description:</b>
        Tests the dataset manager's ability to determine the number of required
        annotations for a project and construct a training dataset.
        Additionally, tests whether saving and updating the dataset manager's
        configuration properly changes its behavior.

        <b>Input data:</b>
        A project with a classification and object detection task.

        <b>Steps:</b>
        1. Get a project with a classification and object detection task,
            and a dataset with one image
        2. Initiate coordinator instance which contains the dataset manager
        3. Fetch the required_images_auto_training from the configurable parameters.
            Increase its value by 5 and save the configurable parameters,
            then reload the dataset manager configuration
        4. Add an image to the project and randomly generate 700 annotations for it
        5. Calculate the number of missing annotations
        6. Check that the number of missing annotations was correctly calculated
            based on the number of provided annotations and the updated
            configurable parameters
        7. Get the training dataset
        8. Check that the training dataset contains the correct number of annotations
        """
        project = fxt_test_dataset_manager_data.project
        detection_node = fxt_test_dataset_manager_data.detection_node
        classification_node = fxt_test_dataset_manager_data.classification_node
        detection_labels = fxt_test_dataset_manager_data.detection_labels
        classification_labels = fxt_test_dataset_manager_data.classification_labels
        dataset_storage = project.get_training_dataset_storage()
        DatasetCounterUseCase.on_project_create(workspace_id=project.workspace_id, project_id=project.id_)

        n_boxes = 50
        dataset = fxt_dataset
        dataset.purpose = DatasetPurpose.TRAINING
        dataset_item = dataset[0]

        n_update_required_images = DatasetCounterConfig().required_images_auto_training + 5  # type: ignore[call-arg]
        new_config = DatasetCounterConfig()  # type: ignore[call-arg]
        new_config.required_images_auto_training = n_update_required_images
        new_config.label_constraint_first_training = True
        conf_params = ComponentParameters(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            component=ComponentType.DATASET_COUNTER,
            id_=ConfigurableParametersRepo.generate_id(),
            task_id=detection_node.id_,
            data=new_config,
        )
        ConfigurableParametersRepo(project.identifier).save(conf_params)

        non_empty_detection_labels = [label for label in detection_labels if not label.is_empty]
        new_annotations = self.create_randomized_annotations(n_boxes, non_empty_detection_labels, classification_labels)
        new_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=dataset_item.annotation_scene.media_identifier,
            media_height=dataset_item.media.height,
            media_width=dataset_item.media.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id=dataset_item.annotation_scene.last_annotator_id,
            annotations=new_annotations,
        )
        AnnotationSceneRepo(dataset_storage.identifier).save(new_annotation_scene)

        DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
            project_id=project.id_, annotation_scene_id=new_annotation_scene.id_
        )
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        dataset_detection = pipeline_dataset_entity.task_datasets[detection_node.id_].get_dataset(
            dataset_storage=dataset_storage
        )
        DatasetCounterUseCase.on_dataset_update(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            task_node_id=detection_node.id_,
            new_dataset_items=[item.id_ for item in dataset_detection],
            deleted_dataset_items=[],
            assigned_dataset_items=[],
            dataset_id=dataset_detection.id_,
        )
        dataset_classification = pipeline_dataset_entity.task_datasets[classification_node.id_].get_dataset(
            dataset_storage=dataset_storage
        )
        DatasetCounterUseCase.on_dataset_update(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            task_node_id=classification_node.id_,
            new_dataset_items=[item.id_ for item in dataset_classification],
            deleted_dataset_items=[],
            assigned_dataset_items=[],
            dataset_id=dataset_classification.id_,
        )
        required_annotations_det = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=detection_node,
        )
        required_annotations_clas = MissingAnnotationsHelper.get_missing_annotations_for_task(
            dataset_storage_identifier=dataset_storage.identifier,
            task_node=classification_node,
        )

        assert required_annotations_det.total_missing_annotations_auto_training == n_update_required_images - 1
        assert required_annotations_clas.total_missing_annotations_auto_training == 0

        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        detection_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[detection_node.id_],
            project_id=project.id_,
            task_node=detection_node,
            dataset_storage=dataset_storage,
        )
        classification_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[classification_node.id_],
            project_id=project.id_,
            task_node=classification_node,
            dataset_storage=dataset_storage,
        )
        assert len(detection_dataset) == 1
        assert len(classification_dataset) == n_boxes

    def test_dataset_reconstruction_after_delete(self, request) -> None:
        """
        <b>Description:</b>
        To test the dataset manager's ability to reconstruct a dataset
        after deleting an item from the dataset.

        <b>Input data:</b>
        A classification project.

        <b>Expected results:</b>
        Test passes if the number of items in the reconstructed dataset
        (after deleting an item) is as expected.

        <b>Steps</b>
        1. Create an annotated classification project with 2 images and update the buffer dataset
        2. Delete an item in the dataset.
        3. Fetch the training dataset again.
        4. Check if the number of items in the reconstructed dataset
            (after deleting an item) is as expected.

        """
        model_template = register_classification_task(request)
        project = generate_random_annotated_project(
            test_case=request,
            name="__Test dataset manager",
            description="",
            model_template_id=model_template,
            number_of_images=2,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        task_node = project.get_trainable_task_nodes()[0]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )

        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage_identifier)

        new_annotation_scenes = list(
            AnnotationSceneRepo(dataset_storage_identifier).get_all_by_kind(
                kind=AnnotationSceneKind.ANNOTATION,
            )
        )

        new_annotation_scenes_states = AnnotationSceneStateRepo(
            dataset_storage_identifier
        ).get_latest_for_annotation_scenes(annotation_scene_ids=[ann_scene.id_ for ann_scene in new_annotation_scenes])
        new_dataset_items = [
            DatasetHelper.annotation_scene_to_dataset_item(
                annotation_scene=scene,
                dataset_storage=dataset_storage,
                subset=Subset.UNASSIGNED,
                annotation_scene_state=new_annotation_scenes_states.get(scene.id_),
            )
            for scene in new_annotation_scenes
        ]
        new_items_dataset = Dataset(items=new_dataset_items, id=DatasetRepo.generate_id())
        DatasetUpdateUseCase._update_dataset_with_new_items(
            new_items_dataset_for_task=new_items_dataset,
            pipeline_dataset_entity=pipeline_dataset_entity,
            dataset_storage_identifier=dataset_storage_identifier,
            project=project,
        )

        request.addfinalizer(
            lambda: PipelineDatasetRepo(dataset_storage_identifier).delete_by_id(pipeline_dataset_entity.id_)
        )

        first_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[task_node.id_],
            project_id=project.id_,
            task_node=task_node,
            dataset_storage=dataset_storage,
        )
        assert len(first_dataset) == 2, "Expected 2 items in the first training dataset"

        # Delete the first image
        first_dataset_item = first_dataset[0]
        if isinstance(first_dataset_item.media, Image):
            DeletionHelpers.delete_image_entity(dataset_storage=dataset_storage, image=first_dataset_item.media)
            dataset_repo = DatasetRepo(dataset_storage.identifier)
            dataset_repo.delete_items_by_dataset_and_media_identifiers(
                dataset_id=pipeline_dataset_entity.task_datasets[task_node.id_].dataset_id,
                media_identifiers=[first_dataset_item.media_identifier],
            )

        new_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[task_node.id_],
            project_id=project.id_,
            task_node=task_node,
            dataset_storage=dataset_storage,
        )
        assert len(new_dataset) == 1, "Expected 1 item in the second training dataset, after deleting one image"

    def test_dataset_manager_subset_consistency(
        self, request, fxt_empty_label_schema, fxt_test_dataset_manager_data
    ) -> None:
        """
        <b>Description:</b>
        Tests that when getting training datasets twice independently, the subsets are the same.

        <b>Input data:</b>
        fxt_test_dataset_manager_data, which includes all entities needed in a task chain project

        <b>Expected results:</b>
        Test passes if the subsets are the same for both training datasets

        <b>Steps</b>
        1. Create images and annotations.
        2. Get the datasets and save a model with those datasets
        3. Create images and annotations again
        4. Get the dataset and assert that the subsets are the same
        """
        project = fxt_test_dataset_manager_data.project
        dataset_storage = project.get_training_dataset_storage()

        # create images
        images = [
            Image(
                name=f"image{i + 1}",
                uploader_id="",
                id=ImageRepo.generate_id(),
                width=100,
                height=100,
                size=100,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
            )
            for i in range(4)
        ]
        # save images
        image_repo = ImageRepo(dataset_storage.identifier)
        for image in images:
            image_repo.save(image)
            request.addfinalizer(lambda: DeletionHelpers.delete_image_entity(dataset_storage, image))

        annotations1 = self.create_randomized_annotations(
            10,
            fxt_test_dataset_manager_data.detection_labels,
            fxt_test_dataset_manager_data.classification_labels,
        )
        annotations2 = self.create_randomized_annotations(
            20,
            fxt_test_dataset_manager_data.detection_labels,
            fxt_test_dataset_manager_data.classification_labels,
        )

        # create annotations
        ann1 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(images[0].id_),
            media_height=images[0].height,
            media_width=images[0].width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations1,
        )
        ann2 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(images[1].id_),
            media_height=images[1].height,
            media_width=images[1].width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations2,
        )
        # save annotations
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        ann_scene_repo.save(ann1)
        ann_scene_repo.save(ann2)
        # get training_datasets
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        first_detection_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[fxt_test_dataset_manager_data.detection_node.id_],
            project_id=project.id_,
            task_node=fxt_test_dataset_manager_data.detection_node,
            dataset_storage=dataset_storage,
        )
        first_classification_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[
                fxt_test_dataset_manager_data.classification_node.id_
            ],
            project_id=project.id_,
            task_node=fxt_test_dataset_manager_data.classification_node,
            dataset_storage=dataset_storage,
        )
        # save subsets
        first_detection_subsets = self.get_subsets_from_dataset(first_detection_dataset)
        first_classification_subsets = self.get_subsets_from_dataset(first_classification_dataset)
        # save dataset
        detection_model = Model(
            project=fxt_test_dataset_manager_data.project,
            model_storage=ModelService.get_active_model_storage(
                project_identifier=project.identifier,
                task_node_id=fxt_test_dataset_manager_data.detection_node.id_,
            ),
            train_dataset=first_detection_dataset,
            configuration=ModelConfiguration(
                ConfigurableParameters(header="Empty parameters"),
                label_schema=fxt_empty_label_schema,
            ),
            id_=ModelRepo.generate_id(),
            data_source_dict={"data.bin": b""},
        )
        classification_model = Model(
            project=fxt_test_dataset_manager_data.project,
            model_storage=ModelService.get_active_model_storage(
                project_identifier=project.identifier,
                task_node_id=fxt_test_dataset_manager_data.classification_node.id_,
            ),
            train_dataset=first_classification_dataset,
            configuration=ModelConfiguration(
                ConfigurableParameters(header="Empty parameters"),
                label_schema=fxt_empty_label_schema,
            ),
            id_=ModelRepo.generate_id(),
            data_source_dict={"data.bin": b""},
        )
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(first_detection_dataset)
        dataset_repo.save_deep(first_classification_dataset)
        request.addfinalizer(lambda: dataset_repo.delete_by_id(first_detection_dataset.id_))
        request.addfinalizer(lambda: dataset_repo.delete_by_id(first_classification_dataset.id_))

        detection_model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier,
            task_node_id=project.get_trainable_task_nodes()[0].id_,
        )
        classification_model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier,
            task_node_id=project.get_trainable_task_nodes()[1].id_,
        )
        ModelRepo(detection_model_storage.identifier).save(detection_model)
        ModelRepo(classification_model_storage.identifier).save(classification_model)
        # new annotations (more shapes)
        for annotation in ann1.annotations:
            annotation.set_labels(
                [
                    ScoredLabel(
                        label_id=fxt_test_dataset_manager_data.detection_labels[0].id_,
                        is_empty=fxt_test_dataset_manager_data.detection_labels[0].is_empty,
                        probability=1.0,
                    ),
                    ScoredLabel(
                        label_id=fxt_test_dataset_manager_data.classification_labels[0].id_,
                        is_empty=fxt_test_dataset_manager_data.classification_labels[0].is_empty,
                        probability=1.0,
                    ),
                ]
            )

        annotations3 = self.create_randomized_annotations(
            10,
            fxt_test_dataset_manager_data.detection_labels,
            fxt_test_dataset_manager_data.classification_labels,
        )
        annotations4 = self.create_randomized_annotations(
            10,
            fxt_test_dataset_manager_data.detection_labels,
            fxt_test_dataset_manager_data.classification_labels,
        )

        ann3 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(images[2].id_),
            media_height=images[2].height,
            media_width=images[2].width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=ann1.annotations[:] + annotations3,
        )
        ann4 = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(images[3].id_),
            media_height=images[3].height,
            media_width=images[3].width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=ann2.annotations[:] + annotations4,
        )
        # save annotations
        ann_scene_repo.save(ann3)
        ann_scene_repo.save(ann4)

        # get training_datasets
        second_detection_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[fxt_test_dataset_manager_data.detection_node.id_],
            project_id=fxt_test_dataset_manager_data.project.id_,
            task_node=fxt_test_dataset_manager_data.detection_node,
            dataset_storage=dataset_storage,
        )
        second_classification_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[
                fxt_test_dataset_manager_data.classification_node.id_
            ],
            project_id=fxt_test_dataset_manager_data.project.id_,
            task_node=fxt_test_dataset_manager_data.classification_node,
            dataset_storage=dataset_storage,
        )
        # get subsets
        second_detection_subsets = self.get_subsets_from_dataset(second_detection_dataset)
        second_classification_subsets = self.get_subsets_from_dataset(second_classification_dataset)
        # check subsets
        for media_id, value in first_detection_subsets.items():
            for roi_id, subset in value.items():
                assert subset == second_detection_subsets[media_id][roi_id]
        for media_id, value in first_classification_subsets.items():
            for roi_id, subset in value.items():
                assert subset == second_classification_subsets[media_id][roi_id]

    def test_suspend_items(self, request, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Tests the ability of the dataset manager to suspend dataset items for a given
        list of annotation_scene_ids, and save/retrieve the suspended dataset to/from
        the database.

        <b>Input data:</b>
        A project with a (single label) detection task and 12 annotated images in it.

        <b>Expected results:</b>
        The dataset manager is able to suspend certain items in its current dataset,
        by setting their `ignored_label_ids` attribute.

        Upon generating a new training dataset, the affected items will have this
        attribute set to a list of labels to ignore.

        <b>Steps</b>
        1. Create project and model with training dataset
        2. Set annotation scene state for the first 3 items in training dataset to
            have 'labels_to_revisit', and
        3. Dataset manager suspends those items in its dataset
        4. Dataset manager creates a new training dataset: Assert that the first 3
            items have their `ignored_label_ids` property set according to the
            labels_to_revisit
        """
        # Step 1
        project = fxt_db_project_service.create_annotated_detection_project(12)
        dataset_storage = fxt_db_project_service.dataset_storage
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )
        fxt_db_project_service.create_and_save_model(0)
        task = project.get_trainable_task_nodes()[0]
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage_identifier)
        dataset = pipeline_dataset_entity.task_datasets[task.id_].get_dataset(
            dataset_storage=fxt_db_project_service.dataset_storage
        )

        # Step 2
        labels_to_revisit = fxt_db_project_service.label_schema_1.get_labels(False)
        label_ids_to_revisit = [lab.id_ for lab in labels_to_revisit]

        # Create annotation scene states for the first few dataset items
        annotation_scene_ids: list[ID] = []
        ann_scene_state_repo = AnnotationSceneStateRepo(fxt_db_project_service.dataset_storage_identifier)
        n_items_to_update = 3
        for item in dataset[0:n_items_to_update]:
            ann_scene_state = AnnotationSceneState(
                media_identifier=item.media_identifier,
                annotation_scene_id=item.annotation_scene.id_,
                labels_to_revisit_full_scene=label_ids_to_revisit,
                unannotated_rois={},
                annotation_state_per_task={task.id_: AnnotationState.ANNOTATED},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            annotation_scene_ids.append(item.annotation_scene.id_)
            ann_scene_state_repo.save(ann_scene_state)
            request.addfinalizer(lambda: ann_scene_state_repo.delete_by_id(ann_scene_state.id_))

        susp_scenes_repo = SuspendedAnnotationScenesRepo(dataset_storage_identifier)
        suspended_scenes_descriptor = SuspendedAnnotationScenesDescriptor(
            id_=susp_scenes_repo.generate_id(),
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            scenes_ids=tuple(annotation_scene_ids),
        )
        susp_scenes_repo.save(suspended_scenes_descriptor)
        request.addfinalizer(lambda: susp_scenes_repo.delete_by_id(suspended_scenes_descriptor.id_))

        # Step 3: Suspend items
        DatasetSuspender.suspend_dataset_items(
            suspended_scenes_descriptor_id=ID(),
            workspace_id=project.workspace_id,
            project_id=project.id_,
        )

        # Step 4: Create training dataset
        training_dataset = construct_and_save_train_dataset_for_task(
            task_dataset_entity=pipeline_dataset_entity.task_datasets[task.id_],
            project_id=project.id_,
            task_node=task,
            dataset_storage=fxt_db_project_service.dataset_storage,
        )
        # Check that `ignored_label_ids` flag is set correctly for the suspended items,
        # and is emtpy for non-affected items
        for index, item in enumerate(training_dataset):
            if (index + 1) <= n_items_to_update:
                assert item.ignored_label_ids == {label.id_ for label in labels_to_revisit}
            else:
                assert not item.ignored_label_ids

    @flaky(max_runs=5)
    def test_dataset_counter_speed(
        self,
        request,
        fxt_test_dataset_manager_data,
        fxt_dataset,
    ) -> None:
        """
        <b>Description:</b>
        Tests the dataset manager's ability to determine the number of required
        annotations for a project and construct a training dataset.
        Additionally, tests whether saving and updating the dataset manager's
        configuration properly changes its behavior.

        <b>Input data:</b>
        A project with a classification and object detection task.

        <b>Steps:</b>
        1. Get a project with a classification and object detection task,
            and a dataset with one image
        2. Add an image to the project and randomly generate 700 annotations for it.
        3. Simulate that the dataset item labels and dataset item count entities already have 10000 dataset items
            stored, to test their performance for large datasets.
        4. Simulate dataset update for the new annotations
        5. Check that the time taken is less than the set maximum time
        """
        # Arrange parameters
        N_DATASET_ITEMS = 10000
        MAXIMUM_TIME = 0.5
        N_BOXES = 50

        # Arrange task chain project
        project = fxt_test_dataset_manager_data.project
        detection_node = fxt_test_dataset_manager_data.detection_node
        detection_labels = fxt_test_dataset_manager_data.detection_labels
        classification_labels = fxt_test_dataset_manager_data.classification_labels
        dataset_storage = project.get_training_dataset_storage()
        DatasetCounterUseCase.on_project_create(workspace_id=project.workspace_id, project_id=project.id_)

        # Create and save new annotations

        dataset = fxt_dataset
        dataset.purpose = DatasetPurpose.TRAINING
        dataset_item = dataset[0]

        non_empty_detection_labels = [label for label in detection_labels if not label.is_empty]
        new_annotations = self.create_randomized_annotations(N_BOXES, non_empty_detection_labels, classification_labels)
        new_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=dataset_item.annotation_scene.media_identifier,
            media_height=dataset_item.media.height,
            media_width=dataset_item.media.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id=dataset_item.annotation_scene.last_annotator_id,
            annotations=new_annotations,
        )
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        request.addfinalizer(lambda: ann_scene_repo.delete_all())
        ann_scene_repo.save(new_annotation_scene)

        DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
            project_id=project.id_, annotation_scene_id=new_annotation_scene.id_
        )
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage.identifier)
        dataset_detection = pipeline_dataset_entity.task_datasets[detection_node.id_].get_dataset(
            dataset_storage=dataset_storage
        )

        # Simulate a dataset item count and dataset item labels collection with 10000 dataset items for the task
        dataset_item_count_repo = DatasetItemCountRepo(
            dataset_storage_identifier=DatasetStorageIdentifier(
                workspace_id=project.workspace_id,
                project_id=project.id_,
                dataset_storage_id=dataset_storage.id_,
            ),
        )
        dataset_item_count = dataset_item_count_repo.get_by_id(id_=detection_node.id_)
        dataset_item_count.n_dataset_items = N_DATASET_ITEMS
        dataset_item_count_repo.save(dataset_item_count)
        request.addfinalizer(lambda: dataset_item_count_repo.delete_all())

        dataset_item_labels_repo = DatasetItemLabelsRepo(dataset_storage.identifier)
        request.addfinalizer(lambda: dataset_item_labels_repo.delete_all())
        dataset_item_labels_list = []
        for _i in range(N_DATASET_ITEMS):
            dataset_item_labels = DatasetItemLabels(
                dataset_item_id=ID(ObjectId()),
                label_ids=[non_empty_detection_labels[0].id_],
            )
            dataset_item_labels_list.append(dataset_item_labels)
        dataset_item_labels_repo.save_many(dataset_item_labels_list)

        # Test the speed of dataset update for a list of new annotations
        time_before = time.time()
        DatasetCounterUseCase.on_dataset_update(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            task_node_id=detection_node.id_,
            new_dataset_items=[item.id_ for item in dataset_detection],
            deleted_dataset_items=[],
            assigned_dataset_items=[],
            dataset_id=dataset_detection.id_,
        )
        if time.time() - time_before > MAXIMUM_TIME:
            raise TimeoutError(f"Updating the dataset counter took more than {MAXIMUM_TIME}.")


def to_scored(label: Label) -> ScoredLabel:
    return ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)
