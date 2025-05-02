# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence
from functools import partial
from typing import cast

import numpy as np
import pytest

from active_learning.storage.repos import ActiveScoreRepo
from active_learning.usecases import ActiveScoresUpdateUseCase, ActiveSetRetrievalUseCase

from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier
from iai_core_py.algorithms.crop.task import CropTask
from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.datasets import Dataset
from iai_core_py.entities.evaluation_result import EvaluationPurpose, EvaluationResult
from iai_core_py.entities.image import Image
from iai_core_py.entities.label_schema import LabelSchema
from iai_core_py.entities.metadata import FloatMetadata, FloatType, MetadataItem
from iai_core_py.entities.model import Model
from iai_core_py.entities.scored_label import ScoredLabel
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.entities.subset import Subset
from iai_core_py.entities.task_environment import TaskEnvironment
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.entities.tensor import Tensor
from iai_core_py.repos import AnnotationSceneRepo, DatasetRepo, EvaluationResultRepo, MetadataRepo

logger = logging.getLogger(__name__)


class TestActiveLearning:
    @staticmethod
    def _generate_float_metadata_for_image(
        dataset_storage: DatasetStorage, image: Image, model: Model, dataset_item_id: ID
    ) -> MetadataItem:
        metadata_repo = MetadataRepo(dataset_storage.identifier)
        data = FloatMetadata(name="aaa", value=3.0, float_type=FloatType.ACTIVE_SCORE)
        metadata_item = MetadataItem(
            id=MetadataRepo.generate_id(),
            data=data,
            dataset_item_id=dataset_item_id,
            media_identifier=image.media_identifier,
            model=model,
        )
        metadata_repo.save(metadata_item)
        return metadata_item

    @staticmethod
    def _generate_tensor_metadata_for_image(
        dataset_storage: DatasetStorage, image: Image, model: Model, dataset_item_id: ID
    ) -> MetadataItem:
        metadata_repo = MetadataRepo(dataset_storage.identifier)
        tensor = Tensor(
            name="representation_vector",
            numpy=np.random.uniform(0, 1, size=(1, 32)),
        )
        metadata_item = MetadataItem(
            id=MetadataRepo.generate_id(),
            data=tensor,
            dataset_item_id=dataset_item_id,
            media_identifier=image.media_identifier,
            model=model,
        )
        metadata_repo.save(metadata_item)
        return metadata_item

    @staticmethod
    def _generate_result_set(
        dataset_storage_identifier: DatasetStorageIdentifier,
        gt_dataset: Dataset,
        pred_dataset: Dataset,
        model: Model,
    ):
        project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
        )
        evaluation_result_repo: EvaluationResultRepo = EvaluationResultRepo(project_identifier)
        # for simplicity, let the whole training dataset be validation
        val_result_set = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=project_identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            ground_truth_dataset=gt_dataset.id_,
            prediction_dataset=pred_dataset.id_,
            purpose=EvaluationPurpose.VALIDATION,
        )
        test_result_set = EvaluationResult(
            id_=EvaluationResultRepo.generate_id(),
            project_identifier=project_identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            ground_truth_dataset=ID(),
            prediction_dataset=ID(),
            purpose=EvaluationPurpose.TEST,
        )
        evaluation_result_repo.save(val_result_set)
        evaluation_result_repo.save(test_result_set)

    @staticmethod
    def _generate_predictions_and_metadata_for_task(
        dataset_storage: DatasetStorage,
        task_node: TaskNode,
        task_label_schema: LabelSchema,
        model: Model,
        images: Sequence[Image],
    ) -> Dataset:
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        labels = task_label_schema.get_labels(True)

        dataset_items: list[DatasetItem] = []
        is_global_task = task_node.task_properties.is_global
        for image in images:
            # Generate a prediction (annotation scene) and persist it
            if is_global_task:
                shape = Rectangle(0, 0, 1, 1)
            else:
                shape = Rectangle(0.3, 0.4, 0.5, 0.6)
            pred_scene = AnnotationScene(
                kind=AnnotationSceneKind.PREDICTION,
                media_identifier=image.media_identifier,
                media_height=30,
                media_width=30,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=[
                    Annotation(
                        shape=shape,
                        labels=[ScoredLabel(label_id=labels[0].id_, is_empty=labels[0].is_empty, probability=0.8)],
                    )
                ],
                task_id=task_node.id_,
            )
            ann_scene_repo.save(pred_scene)
            # Generate metadata and dataset item
            dataset_item_id = DatasetRepo.generate_id()
            tensor_metadata = TestActiveLearning._generate_tensor_metadata_for_image(
                dataset_storage=dataset_storage,
                image=image,
                model=model,
                dataset_item_id=dataset_item_id,
            )
            float_metadata = TestActiveLearning._generate_float_metadata_for_image(
                dataset_storage=dataset_storage,
                image=image,
                model=model,
                dataset_item_id=dataset_item_id,
            )
            dataset_items.append(
                DatasetItem(
                    id_=dataset_item_id,
                    media=image,
                    roi=pred_scene.annotations[0] if is_global_task else None,
                    annotation_scene=pred_scene,
                    metadata=[tensor_metadata, float_metadata],
                )
            )

        # Generate an output dataset containing the predictions
        output_dataset = Dataset(
            id=DatasetRepo.generate_id(),
            items=dataset_items,
            label_schema_id=task_label_schema.id_,
        )
        DatasetRepo(dataset_storage.identifier).save(output_dataset)
        return output_dataset

    @staticmethod
    def _generate_training_artifacts(
        dataset_storage: DatasetStorage,
        task_nodes: Sequence[TaskNode],
        label_schemas: Sequence[LabelSchema],
        models: Sequence[Model],
        annotated_images: Sequence[Image],
        unannotated_images: Sequence[Image],
        training_dataset: Dataset,
    ) -> tuple[tuple[Dataset, Dataset], ...]:
        ProjectIdentifier(
            workspace_id=dataset_storage.workspace_id,
            project_id=dataset_storage.project_id,
        )
        annotated_inferred_datasets_out: list[Dataset] = []
        unannotated_inferred_datasets_out: list[Dataset] = []
        for task_node, schema, model in zip(task_nodes, label_schemas, models):
            # annotated
            annotated_inferred_output_dataset = TestActiveLearning._generate_predictions_and_metadata_for_task(
                dataset_storage=dataset_storage,
                task_node=task_node,
                task_label_schema=schema,
                model=model,
                images=annotated_images,
            )
            annotated_inferred_datasets_out.append(annotated_inferred_output_dataset)
            TestActiveLearning._generate_result_set(
                dataset_storage_identifier=dataset_storage.identifier,
                gt_dataset=training_dataset,
                pred_dataset=annotated_inferred_output_dataset,
                model=model,
            )
            # unannotated
            unannotated_inferred_output_dataset = TestActiveLearning._generate_predictions_and_metadata_for_task(
                dataset_storage=dataset_storage,
                task_node=task_node,
                task_label_schema=schema,
                model=model,
                images=unannotated_images,
            )
            unannotated_inferred_datasets_out.append(unannotated_inferred_output_dataset)
        return tuple(
            (ann_ds, unann_ds)
            for ann_ds, unann_ds in zip(annotated_inferred_datasets_out, unannotated_inferred_datasets_out)
        )

    @pytest.mark.parametrize(
        "active_learning_mode",
        [
            "task",
            "project",
        ],
        ids=[
            "task level active learning",
            "project level active learning",
        ],
    )
    def test_active_learning_before_training(
        self,
        active_learning_mode,
        fxt_db_project_service,
    ) -> None:
        """
        <b>Description:</b>
        Test the ability to get media suggestions from the active learning module before the first round of training.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        It is possible to pull an active set before training.
        The content of the active set is consistent and does not contain duplicates.

        <b>Steps</b>
        1. Create a detection project with some annotated images and 4 unannotated ones
        2. Inform AL about the new media
        3. Request an active set of size 2. The expected output should contain 2 items
           from the unannotated set
        4. Request an active set of size 3. The expected output should contain 2 items
           from the unannotated set (because there are only 4 in total, and 2 are seen),
           different from the ones in the first active set
        """
        db_service = fxt_db_project_service

        project = db_service.create_annotated_detection_project(num_images_per_label=6)
        dataset_storage = db_service.dataset_storage
        unannotated_images = [db_service.create_and_save_random_image(name=f"unannotated_img_{i}") for i in range(4)]
        annotated_media_ids = [item.media_identifier for item in db_service.dataset]
        unannotated_media_ids = [img.media_identifier for img in unannotated_images]
        det_task = db_service.task_node_1
        user_id = ID("dummy_user")

        # Step 2: inform AL about the new media. This will create default active scores.
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=(annotated_media_ids + unannotated_media_ids),
        )

        if active_learning_mode == "project":
            get_active_set_fn = ActiveSetRetrievalUseCase.get_active_set_project_level
        else:
            get_active_set_fn = partial(
                ActiveSetRetrievalUseCase.get_active_set_task_level,
                task_id=det_task.id_,
            )

        # Step 3: Request an active set of size 2
        active_set_1 = get_active_set_fn(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        # Expect 2 items from the unannotated set
        assert len(active_set_1) == 2
        assert set(active_set_1).issubset(set(unannotated_media_ids))

        # Step 4: Request an active set of size 3
        active_set_2 = get_active_set_fn(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=3,
            user_id=user_id,
        )
        # Expect 2 items from the unannotated set
        assert len(active_set_2) == 2
        assert set(active_set_2).issubset(set(unannotated_media_ids))
        assert set(active_set_2).isdisjoint(set(active_set_1))

    @pytest.mark.parametrize(
        "active_learning_mode",
        [
            "task",
            "project",
        ],
        ids=[
            "task level active learning",
            "project level active learning",
        ],
    )
    def test_active_learning_after_training(
        self,
        active_learning_mode,
        fxt_db_project_service,
    ) -> None:
        """
        <b>Description:</b>
        Test the ability to get media suggestions from the active learning module after training once.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        It is possible to pull an active set after training.
        The content of the active set is consistent and does not contain duplicates.
        TODO the next property will change in CVS-88037
        Active learning does not reset after successive rounds of training.

        <b>Steps</b>
        1. Create a detection project with some annotated images and 4 unannotated ones
        2. Inform AL about the new media
        3. Create output datasets and metadata, to simulate the artifacts of a training
           job, which includes evaluation on annotated and inference on unannotated set
        4. Notify AL about the new output datasets
        5. Verify that the active scores are updated in the DB
        6. Request an active set of size 2. The expected output should contain 2 items
           from the unannotated set
        7. Create new output datasets and metadata, to simulate the effect of
           a second training round with inference
        8. Request an active set of size 2. The expected output should contain 2 items
           from the unannotated set, different from the ones in the first active set
           TODO the expected output will change with CVS-88037
        9. Upload 3 new unannotated media.
        10. Request an active set of size 2. The expected output should contain 2 items
            selected among the newly uploaded ones
        """
        db_service = fxt_db_project_service

        user_id = ID("dummy_user")
        project = db_service.create_annotated_detection_project(num_images_per_label=6)
        det_task = db_service.task_node_1
        det_label_schema = db_service.label_schema_1
        det_model = db_service.create_and_save_model(task_node_index=0)
        dataset_storage = db_service.dataset_storage
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )
        train_annotated_images = [
            cast("Image", item.media) for item in db_service.dataset if item.subset == Subset.TRAINING
        ]
        unannotated_images = [db_service.create_and_save_random_image(name=f"unannotated_img_{i}") for i in range(4)]
        annotated_media_ids = [item.media_identifier for item in db_service.dataset]
        unannotated_media_ids = [img.media_identifier for img in unannotated_images]

        # Step 2: inform AL about the new media. This will create default active scores.
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=(annotated_media_ids + unannotated_media_ids),
        )

        if active_learning_mode == "project":
            get_active_set_fn = ActiveSetRetrievalUseCase.get_active_set_project_level
        else:
            get_active_set_fn = partial(
                ActiveSetRetrievalUseCase.get_active_set_task_level,
                task_id=det_task.id_,
            )

        # Step 3: create output datasets (predictions), metadata and result sets
        # to simulate the output of a training job
        (
            train_dataset_with_predictions,
            unannotated_dataset_with_predictions,
        ) = TestActiveLearning._generate_training_artifacts(
            dataset_storage=dataset_storage,
            task_nodes=(det_task,),
            label_schemas=(det_label_schema,),
            models=(det_model,),
            annotated_images=train_annotated_images,
            unannotated_images=unannotated_images,
            training_dataset=db_service.training_dataset,
        )[0]

        # Step 4: notify AL about the new output datasets
        ActiveScoresUpdateUseCase.on_output_datasets_and_metadata_created(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            task_node_id=det_task.id_,
            model_storage_id=det_model.model_storage.id_,
            model_id=det_model.id_,
            unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions.id_,
            annotated_dataset_id=db_service.training_dataset.id_,
            train_dataset_with_predictions_id=train_dataset_with_predictions.id_,
            asynchronous=False,
        )

        # Step 5: verify that the unannotated items scores are updated in the DB
        active_score_repo = ActiveScoreRepo(dataset_storage_identifier)
        active_scores = active_score_repo.get_all()
        non_default_active_scores = [s for s in active_scores if s.pipeline_score < 1]
        non_default_active_scores_media = {s.media_identifier for s in non_default_active_scores}
        assert len(non_default_active_scores) == 4
        assert non_default_active_scores_media == set(unannotated_media_ids)

        # Step 6: Request an active set of size 2
        active_set_1 = get_active_set_fn(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        # Expect 2 items from the unannotated set
        assert len(active_set_1) == 2
        assert set(active_set_1).issubset(set(unannotated_media_ids))

        # Step 7: create new training artifacts
        (
            train_dataset_with_predictions,
            unannotated_dataset_with_predictions,
        ) = TestActiveLearning._generate_training_artifacts(
            dataset_storage=dataset_storage,
            task_nodes=(det_task,),
            label_schemas=(det_label_schema,),
            models=(det_model,),
            annotated_images=train_annotated_images,
            unannotated_images=unannotated_images,
            training_dataset=db_service.training_dataset,
        )[0]

        # Step 8: Request an active set of size 2
        active_set_2 = get_active_set_fn(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        # Expect 2 items from the unannotated set
        assert len(active_set_2) == 2
        assert set(active_set_2).issubset(set(unannotated_media_ids))
        assert set(active_set_2).isdisjoint(set(active_set_1))

        # Step 9: upload 3 more unannotated images
        new_unannotated_images = [
            db_service.create_and_save_random_image(name=f"unannotated_img_{i}") for i in range(4, 7)
        ]
        new_unannotated_media_ids = [img.media_identifier for img in new_unannotated_images]
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=new_unannotated_media_ids,
        )

        # Step 10: Request an active set of size 2
        active_set_3 = get_active_set_fn(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        # Expect 2 items from the new unannotated set
        assert len(active_set_3) == 2
        assert set(active_set_3).issubset(set(new_unannotated_media_ids))

    def test_suggestions_reset_on_depletion(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Test the active suggestions reset after the AL runs out of new media to suggest.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        It is always possible to pull an active set.
        After all the media are presented to the user, the suggestions will reset.

        <b>Steps</b>
        1. Create a detection project with some annotated images and 4 unannotated ones
        2. Inform AL about the new media
        3. Request an active set of size 2. The expected output should contain 2 items
           from the unannotated set
        4. Request an active set of size 2. The expected output should contain 2 items
           from the unannotated set different from the ones in the first active set.
        5, Request an active set of size 2. The expected output should contain 2 items
           from the unannotated set, already present in the first or second active set.
        """
        db_service = fxt_db_project_service

        user_id = ID("dummy_user")
        project = db_service.create_annotated_detection_project(num_images_per_label=6)
        dataset_storage = db_service.dataset_storage
        unannotated_images = [db_service.create_and_save_random_image(name=f"unannotated_img_{i}") for i in range(4)]
        annotated_media_ids = [item.media_identifier for item in db_service.dataset]
        unannotated_media_ids = [img.media_identifier for img in unannotated_images]

        # Step 2: inform AL about the new media. This will create default active scores.
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=(annotated_media_ids + unannotated_media_ids),
        )

        # Step 3: Request an active set of size 2
        active_set_1 = ActiveSetRetrievalUseCase.get_active_set_project_level(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        # Expect 2 items from the unannotated set
        assert len(active_set_1) == 2
        assert set(active_set_1).issubset(set(unannotated_media_ids))

        # Step 4: Request an active set of size 2
        active_set_2 = ActiveSetRetrievalUseCase.get_active_set_project_level(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        # Expect 2 items from the unannotated set
        assert len(active_set_2) == 2
        assert set(active_set_2).issubset(set(unannotated_media_ids))
        assert set(active_set_2).isdisjoint(set(active_set_1))

        # Step 5: Request an active set of size 2
        active_set_3 = ActiveSetRetrievalUseCase.get_active_set_project_level(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        assert len(active_set_3) == 2
        assert set(active_set_3).issubset(set(unannotated_media_ids))

    @pytest.mark.parametrize(
        "active_learning_mode",
        ["task", "project"],
        ids=["task level active learning", "project level active learning"],
    )
    def test_active_learning_task_chain(self, active_learning_mode, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Test the ability to update the active scores and get active suggestions in
        a task chain project.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        It is always possible to pull an active set.
        The content of the active set is consistent and does not contain duplicates.

        <b>Steps</b>
        1. Create a det -> cls project with some annotated images and 4 unannotated ones
        2. Inform AL about the new media
        3. Create output datasets and metadata, to simulate the artifacts of a training
           job, which includes evaluation on annotated and inference on unannotated set
        4. Notify AL about the new output datasets
        5. Request an active set of size 2. The expected output should contain 2 items
            from the unannotated set
        """
        db_service = fxt_db_project_service
        user_id = ID("dummy_user")

        # Step 1: create project with annotated and unannotated images
        project = db_service.create_annotated_detection_classification_project(num_images_per_label=6)
        dataset_storage = db_service.dataset_storage
        train_annotated_images = [
            cast("Image", item.media) for item in db_service.dataset if item.subset == Subset.TRAINING
        ]
        unannotated_images = [db_service.create_and_save_random_image(name=f"unannotated_img_{i}") for i in range(4)]
        annotated_media_ids = [item.media_identifier for item in db_service.dataset]
        unannotated_media_ids = [img.media_identifier for img in unannotated_images]
        det_task = db_service.task_node_1
        det_label_schema = db_service.label_schema_1
        det_model = db_service.create_and_save_model(task_node_index=0)
        cls_task = db_service.task_node_2
        cls_label_schema = db_service.label_schema_2
        cls_model = db_service.create_and_save_model(task_node_index=1)
        det_train_dataset = db_service.training_dataset
        cls_train_dataset = CropTask(
            task_environment=TaskEnvironment(
                model_template=cls_model.model_storage.model_template,
                model=cls_model,
                hyper_parameters=ConfigurableParameters(header="Empty parameters"),
                label_schema=db_service.label_schema,
            )
        ).infer(dataset=det_train_dataset)
        DatasetRepo(dataset_storage.identifier).save(cls_train_dataset)

        # Step 2: inform AL about the new media. This will create default active scores.
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=(annotated_media_ids + unannotated_media_ids),
        )

        # Step 3: create output datasets (predictions), metadata and result sets
        # to simulate the output of a training job
        ann_and_unann_pred_datasets = TestActiveLearning._generate_training_artifacts(
            dataset_storage=dataset_storage,
            task_nodes=(det_task, cls_task),
            label_schemas=(det_label_schema, cls_label_schema),
            models=(det_model, cls_model),
            annotated_images=train_annotated_images,
            unannotated_images=unannotated_images,
            training_dataset=det_train_dataset,
        )
        (
            det_train_dataset_with_predictions,
            det_unannotated_dataset_with_predictions,
        ) = ann_and_unann_pred_datasets[0]
        (
            cls_train_dataset_with_predictions,
            cls_unannotated_dataset_with_predictions,
        ) = ann_and_unann_pred_datasets[1]

        # Step 4: notify AL about the new output datasets
        ActiveScoresUpdateUseCase.on_output_datasets_and_metadata_created(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            task_node_id=det_task.id_,
            model_storage_id=det_model.model_storage.id_,
            model_id=det_model.id_,
            unannotated_dataset_with_predictions_id=det_unannotated_dataset_with_predictions.id_,
            annotated_dataset_id=det_train_dataset.id_,
            train_dataset_with_predictions_id=det_train_dataset_with_predictions.id_,
            asynchronous=False,
        )
        ActiveScoresUpdateUseCase.on_output_datasets_and_metadata_created(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            task_node_id=cls_task.id_,
            model_storage_id=cls_model.model_storage.id_,
            model_id=cls_model.id_,
            unannotated_dataset_with_predictions_id=cls_unannotated_dataset_with_predictions.id_,
            annotated_dataset_id=cls_train_dataset.id_,
            train_dataset_with_predictions_id=cls_train_dataset_with_predictions.id_,
            asynchronous=False,
        )

        if active_learning_mode == "project":
            get_active_set_fn = ActiveSetRetrievalUseCase.get_active_set_project_level
        else:
            get_active_set_fn = partial(
                ActiveSetRetrievalUseCase.get_active_set_task_level,
                task_id=det_task.id_,
            )

        # Step 5: Request an active set of size 2
        active_set_1 = get_active_set_fn(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=2,
            user_id=user_id,
        )
        # Expect 2 items from the unannotated set
        assert len(active_set_1) == 2
        assert set(active_set_1).issubset(set(unannotated_media_ids))

    def test_suggestions_after_deletion(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Test the active learning after deleting some media.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        It is always possible to pull an active set. Deleted media are not suggested.

        <b>Steps</b>
        1. Create a detection project with some annotated images and 4 unannotated ones
        2. Inform AL about the new media
        3. Request an active set of size 1. The expected output should contain 1 item
           from the unannotated set
        4. Delete 1 item from the set of non-suggested unannotated ones
        5. Request an active set of size 3. The expected output should contain only 2
           items from the unannotated set, different from the one in the 1st active set
        """
        db_service = fxt_db_project_service
        user_id = ID("dummy_user")

        project = db_service.create_annotated_detection_project(num_images_per_label=6)
        dataset_storage = db_service.dataset_storage
        unannotated_images = [db_service.create_and_save_random_image(name=f"unannotated_img_{i}") for i in range(4)]
        annotated_media_ids = [item.media_identifier for item in db_service.dataset]
        unannotated_media_ids = [img.media_identifier for img in unannotated_images]

        # Step 2: inform AL about the new media. This will create default active scores.
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=(annotated_media_ids + unannotated_media_ids),
        )

        # Step 3: Request an active set of size 1
        active_set_1 = ActiveSetRetrievalUseCase.get_active_set_project_level(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=1,
            user_id=user_id,
        )
        assert len(active_set_1) == 1
        assert set(active_set_1).issubset(set(unannotated_media_ids))

        # Step 4: Delete one media
        identifier_to_delete = (set(unannotated_media_ids) - set(active_set_1)).pop()
        ActiveScoresUpdateUseCase.on_media_deleted(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=[identifier_to_delete],
            asynchronous=False,
        )

        # Step 5: Request an active set of size 3
        active_set_2 = ActiveSetRetrievalUseCase.get_active_set_project_level(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=3,
            user_id=user_id,
        )
        # Expect two items, different from the first active set and the deleted one
        assert len(active_set_2) == 2
        assert set(active_set_2).isdisjoint(set(active_set_1))
        assert identifier_to_delete not in active_set_2

    def test_suggestions_randomness_before_training(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Verify that before training the suggested media are picked seemingly randomly,
        without any visible pattern due to their upload order.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The suggestions contain samples from different classes, not just one.

        <b>Steps</b>
        1. Create a detection project
        2. Create 25 unannotated images of one type (A) and 25 of another (25)
        3. Upload the two sets of unannotated images separately
        2. Inform AL about the new media
        3. Request an active set of size 25. The expected output should contain items
           from both sets A and B
        """
        db_service = fxt_db_project_service
        user_id = ID("dummy_user")

        project = db_service.create_annotated_detection_project(num_images_per_label=6)
        dataset_storage = db_service.dataset_storage
        unannotated_images_a = [db_service.create_and_save_random_image(name=f"img_A_{i}") for i in range(25)]
        unannotated_images_b = [db_service.create_and_save_random_image(name=f"img_B_{i}") for i in range(25)]
        unannotated_media_a_ids = [img.media_identifier for img in unannotated_images_a]
        unannotated_media_b_ids = [img.media_identifier for img in unannotated_images_b]

        # Step 2: inform AL about the new media. This will create default active scores.
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=unannotated_media_a_ids,
        )
        ActiveScoresUpdateUseCase.on_media_uploaded(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            media_identifiers=unannotated_media_b_ids,
        )

        # Step 3: Request an active set of size 25
        active_set = ActiveSetRetrievalUseCase.get_active_set_project_level(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            size=25,
            user_id=user_id,
        )
        media_a_present = any(active_item in unannotated_media_a_ids for active_item in active_set)
        media_b_present = any(active_item in unannotated_media_b_ids for active_item in active_set)
        assert len(active_set) == 25
        assert media_a_present and media_b_present
