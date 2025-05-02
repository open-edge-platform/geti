#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#
from copy import copy
from unittest.mock import ANY, call, patch

import pytest

from sc_sdk.entities.datasets import NullDataset
from sc_sdk.entities.model import Model, ModelFormat, ModelOptimizationType, ModelStatus, NullModel
from sc_sdk.repos import ModelRepo, ProjectRepo
from sc_sdk.repos.model_repo import ModelStatusFilter
from sc_sdk.repos.storage.binary_repos import ModelBinaryRepo
from tests.test_helpers import empty_model_configuration


class TestModelRepo:
    def test_indexes(self, fxt_model_storage) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)

        indexes_names = set(model_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1_model_storage_id_-1__id_1",
            "model_storage_id_-1_version_-1",
            "previous_trained_revision_id_-1",
            "model_format_-1_training_duration_-1",
        }

    def test_save(self, request, fxt_model_storage, fxt_model) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        assert len(fxt_model.model_adapters) == 1, "Tested model should have one adapter"
        assert fxt_model.exportable_code_adapter is not None, "Tested model should have exportable code"
        request.addfinalizer(lambda: model_repo.delete_by_id(fxt_model.id_))

        with patch.object(ModelBinaryRepo, "save", return_value=None) as mock_save:
            model_repo.save(fxt_model)

        assert mock_save.call_count == 2
        mock_save.assert_has_calls(
            calls=[
                call(dst_file_name=ANY, data_source=ANY, make_unique=True),
                call(dst_file_name="exportable_code.whl", data_source=ANY, make_unique=True),
            ],
            any_order=True,
        )
        assert not fxt_model.ephemeral

    def test_save_many(self, request, fxt_model_storage, fxt_model) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)

        with patch.object(model_repo, "save") as mock_save:
            model_repo.save_many([fxt_model, fxt_model])

        assert mock_save.call_count == 2

    def test_get_all_by_status_and_type(
        self, request, fxt_empty_project, fxt_model_storage, fxt_model_success, fxt_model_optimized, fxt_model_failed
    ) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save_many([fxt_model_success, fxt_model_optimized, fxt_model_failed])
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            found_trained_models = list(
                model_repo.get_all_by_status_and_type(
                    model_status_filter=ModelStatusFilter.TRAINED,
                    include_optimized_models=True,
                )
            )
            assert len(found_trained_models) == 2
            assert fxt_model_success in found_trained_models
            assert fxt_model_optimized in found_trained_models

            found_trained_base_models = list(
                model_repo.get_all_by_status_and_type(
                    model_status_filter=ModelStatusFilter.TRAINED,
                    include_optimized_models=False,
                )
            )
            assert len(found_trained_base_models) == 1
            assert fxt_model_success in found_trained_base_models

            found_base_models = list(
                model_repo.get_all_by_status_and_type(
                    model_status_filter=ModelStatusFilter.ALL,
                    include_optimized_models=False,
                )
            )
            assert len(found_base_models) == 2
            assert fxt_model_success in found_base_models
            assert fxt_model_failed in found_base_models

    def test_get_latest_successful_version(
        self, request, fxt_model_storage, fxt_model_success, fxt_model_failed
    ) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        assert model_repo.get_latest_successful_version() == 0
        model_success_1 = fxt_model_success
        model_success_1.version = 1
        model_success_2 = copy(fxt_model_success)
        model_success_2.id_ = model_repo.generate_id()
        model_success_2.version = 2
        fxt_model_failed.version = 2

        # commit a successful model
        model_repo.save(model_success_1)
        assert model_repo.get_latest_successful_version() == 1

        # commit a failed model
        model_repo.save(fxt_model_failed)
        assert model_repo.get_latest_successful_version() == 1

        # commit a newer successful model
        model_repo.save(model_success_2)
        assert model_repo.get_latest_successful_version() == 2

    @pytest.mark.parametrize("leaf_only", [False, True])
    def test_get_optimized_models_by_trained_revision_id(
        self, request, leaf_only, fxt_empty_project, fxt_model_storage, fxt_model_success, fxt_training_framework
    ) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        base_model = fxt_model_success
        base_model_2 = copy(base_model)
        base_model_2.id_ = model_repo.generate_id()
        opt_model_1 = Model(
            project=fxt_empty_project,
            model_storage=base_model.model_storage,
            train_dataset=base_model.train_dataset,
            configuration=base_model.configuration,
            id_=model_repo.generate_id(),
            previous_trained_revision=base_model,
            previous_revision=base_model,
            data_source_dict={"inference_model.bin": b"weights_data"},
            training_framework=fxt_training_framework,
            optimization_type=ModelOptimizationType.POT,
        )
        opt_model_2 = Model(
            project=fxt_empty_project,
            model_storage=base_model.model_storage,
            train_dataset=base_model.train_dataset,
            configuration=base_model.configuration,
            id_=model_repo.generate_id(),
            previous_trained_revision=base_model,
            previous_revision=opt_model_1,
            data_source_dict={"inference_model.bin": b"weights_data"},
            training_framework=fxt_training_framework,
            optimization_type=ModelOptimizationType.POT,
        )
        opt_model_other_lineage = Model(
            project=fxt_empty_project,
            model_storage=base_model.model_storage,
            train_dataset=base_model.train_dataset,
            configuration=base_model.configuration,
            id_=model_repo.generate_id(),
            previous_trained_revision=base_model_2,
            previous_revision=base_model_2,
            data_source_dict={"inference_model.bin": b"weights_data"},
            training_framework=fxt_training_framework,
            optimization_type=ModelOptimizationType.POT,
        )
        model_repo.save_many([base_model, base_model_2, opt_model_1, opt_model_2, opt_model_other_lineage])
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            found_models = model_repo.get_optimized_models_by_trained_revision_id(
                trained_revision_id=base_model.id_,
                model_status_filter=ModelStatusFilter.ALL,
                leaf_only=leaf_only,
            )

        if leaf_only:
            assert len(found_models) == 1
            assert opt_model_1 not in found_models
        else:
            assert len(found_models) == 2
            assert opt_model_1 in found_models
        assert opt_model_2 in found_models

    def test_get_optimized_models_by_base_model_id(
        self, request, fxt_empty_project, fxt_model_storage, fxt_model_success, fxt_training_framework
    ) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        base_model = fxt_model_success
        base_model_2 = copy(base_model)
        base_model_2.id_ = model_repo.generate_id()
        opt_model_1 = Model(
            project=fxt_empty_project,
            model_storage=base_model.model_storage,
            train_dataset=base_model.train_dataset,
            configuration=base_model.configuration,
            id_=model_repo.generate_id(),
            previous_trained_revision=base_model,
            previous_revision=base_model,
            data_source_dict={"inference_model.bin": b"weights_data"},
            training_framework=fxt_training_framework,
            optimization_type=ModelOptimizationType.POT,
        )
        opt_model_2 = Model(
            project=fxt_empty_project,
            model_storage=base_model.model_storage,
            train_dataset=base_model.train_dataset,
            configuration=base_model.configuration,
            id_=model_repo.generate_id(),
            previous_trained_revision=base_model,
            previous_revision=opt_model_1,
            data_source_dict={"inference_model.bin": b"weights_data"},
            training_framework=fxt_training_framework,
            optimization_type=ModelOptimizationType.POT,
        )
        opt_model_other_lineage = Model(
            project=fxt_empty_project,
            model_storage=base_model.model_storage,
            train_dataset=base_model.train_dataset,
            configuration=base_model.configuration,
            id_=model_repo.generate_id(),
            previous_trained_revision=base_model_2,
            previous_revision=base_model_2,
            data_source_dict={"inference_model.bin": b"weights_data"},
            training_framework=fxt_training_framework,
            optimization_type=ModelOptimizationType.POT,
        )
        model_repo.save_many([base_model, base_model_2, opt_model_1, opt_model_2, opt_model_other_lineage])
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            found_models = list(model_repo.get_optimized_models_by_base_model_id(base_model_id=base_model.id_))

        assert len(found_models) == 2
        assert opt_model_1 in found_models
        assert opt_model_2 in found_models

    def test_get_all_equivalent_model_ids(
        self, request, fxt_empty_project, fxt_model_storage, fxt_training_framework
    ) -> None:
        """
        Models:
            Models version 1: M1 (base) -> M2 (MO)
            Models version 2: M3 (base) -> M4 (MO) -> M5 (ONNX) -> m6 (POT)

        Expected:
            f(M1) == [M1, M2]
            f(M2) == [M1, M2]
            f(M3) == [M3, M4, M5]
            f(M4) == [M3, M4, M5]
            f(M5) == [M3, M4, M5]
            f(M6) == [M6]
        """
        project = fxt_empty_project
        model_storage = fxt_model_storage
        model_repo = ModelRepo(model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        data = b"Hello world!"
        # Models version 1: M1(base) → M2(MO)
        m1 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            data_source_dict={"test_data": data},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.BASE_FRAMEWORK,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.NONE,
            version=1,
        )
        m2 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m1,
            data_source_dict={"test_data": data},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.OPENVINO,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.MO,
            version=1,
        )
        # Models version 2: M3 (base) → M4 (MO) → M5 (ONNX) -> M6 (POT)
        m3 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            data_source_dict={"test_data": data},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.BASE_FRAMEWORK,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.ONNX,
            version=2,
        )
        m4 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m3,
            data_source_dict={"test_data": data},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.OPENVINO,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.MO,
            version=2,
        )
        m5 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m3,
            data_source_dict={"test_data": data},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.ONNX,
            has_xai_head=False,
            optimization_type=ModelOptimizationType.ONNX,
            version=2,
        )
        m6 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m3,
            data_source_dict={"test_data": data},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.OPENVINO,
            has_xai_head=False,
            optimization_type=ModelOptimizationType.POT,
            version=2,
        )
        model_repo.save_many([m1, m2, m3, m4, m5, m6])

        assert model_repo.get_all_equivalent_model_ids(m1) == (m1.id_, m2.id_)
        assert model_repo.get_all_equivalent_model_ids(m2) == (m1.id_, m2.id_)
        assert model_repo.get_all_equivalent_model_ids(m3) == (m3.id_, m4.id_, m5.id_)
        assert model_repo.get_all_equivalent_model_ids(m4) == (m3.id_, m4.id_, m5.id_)
        assert model_repo.get_all_equivalent_model_ids(m5) == (m3.id_, m4.id_, m5.id_)
        assert model_repo.get_all_equivalent_model_ids(m6) == (m6.id_,)

    def test_has_models(
        self, request, fxt_empty_project, fxt_model_storage, fxt_model_success, fxt_model_failed
    ) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())

        model_repo.save(fxt_model_failed)
        assert model_repo.has_models(model_status_filter=ModelStatusFilter.ALL)
        assert not model_repo.has_models(model_status_filter=ModelStatusFilter.IMPROVED)

        model_repo.save(fxt_model_success)
        assert model_repo.has_models(model_status_filter=ModelStatusFilter.IMPROVED)

    def test_get_latest(
        self, request, fxt_empty_project, fxt_model_storage, fxt_model_success, fxt_model_failed, fxt_model_optimized
    ) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            # Test when no model is present
            latest_model = model_repo.get_latest()
            assert isinstance(latest_model, NullModel)

            # Test after adding two models: one failed and one successful
            model_repo.save_many([fxt_model_success, fxt_model_failed])
            latest_model = model_repo.get_latest()
            assert latest_model == fxt_model_failed
            latest_model_successful = model_repo.get_latest(model_status_filter=ModelStatusFilter.IMPROVED)
            assert latest_model_successful == fxt_model_success

            # Test after adding one optimized model
            model_repo.save(fxt_model_optimized)
            latest_model_successful = model_repo.get_latest(model_status_filter=ModelStatusFilter.IMPROVED)
            assert latest_model_successful == fxt_model_success
            latest_model_successful_optimized = model_repo.get_latest(
                model_status_filter=ModelStatusFilter.IMPROVED, include_optimized_models=True
            )
            assert latest_model_successful_optimized == fxt_model_optimized

    def test_get_latest_model_for_inference(
        self, request, fxt_empty_project, fxt_model_storage, fxt_training_framework
    ) -> None:
        """
        Models:
            Models version 1: M1 (base) -> M2 (MO)
            Models version 2: M3 (base) -> M4 (MO) -> M5 (MO) -> M6 (ONNX)

        Expected:
            The latest model for inference is M4 (the first one generated after the base model).
        """
        project = fxt_empty_project
        model_storage = fxt_model_storage
        model_repo = ModelRepo(model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        m1 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.BASE_FRAMEWORK,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.NONE,
            version=1,
        )
        m2 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m1,
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.OPENVINO,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.MO,
            version=1,
        )
        m3 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.BASE_FRAMEWORK,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.NONE,
            version=2,
        )
        m4 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m3,
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.OPENVINO,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.MO,
            version=2,
        )
        m5 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m3,
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.OPENVINO,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.MO,
            version=2,
        )
        m6 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            previous_trained_revision=m3,
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.ONNX,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.ONNX,
            version=2,
        )
        model_repo.save_many([m1, m2, m3, m4, m5, m6])
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            inference_model = model_repo.get_latest_model_for_inference()
            inference_model_id = model_repo.get_latest_model_id_for_inference()
            inference_model_for_m1 = model_repo.get_latest_model_for_inference(base_model_id=m1.id_)

        assert inference_model == m4
        assert inference_model_id == inference_model.id_
        assert inference_model_for_m1 == m2

    def test_get_latest_with_latest_version(
        self, request, fxt_empty_project, fxt_model_storage, fxt_training_framework
    ) -> None:
        # Model ID should not be used to determine the latest model for inference
        project = fxt_empty_project
        model_storage = fxt_model_storage
        model_repo = ModelRepo(model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        m1 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.BASE_FRAMEWORK,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.NONE,
            version=1,
        )
        m2 = Model(
            project=project,
            model_storage=model_storage,
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=ModelRepo.generate_id(),
            data_source_dict={"test_data": b"weights_data"},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.SUCCESS,
            model_format=ModelFormat.BASE_FRAMEWORK,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.NONE,
            version=2,
        )
        # m1.id > m2.id but m2.version > m1.version
        m1.id_ = ModelRepo.generate_id()
        model_repo.save(m2)
        model_repo.save(m1)
        inference_model = model_repo.get_latest()
        assert inference_model == m2

    def test_update_model_status(self, request, fxt_empty_project, fxt_model_storage, fxt_model) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save(fxt_model)

        model_repo.update_model_status(model=fxt_model, model_status=ModelStatus.TRAINED_NO_STATS)

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            model_reloaded = model_repo.get_by_id(fxt_model.id_)
        assert model_reloaded.model_status == ModelStatus.TRAINED_NO_STATS

    def test_update_training_duration(self, request, fxt_empty_project, fxt_model_storage, fxt_model) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save(fxt_model)

        model_repo.update_training_duration(model=fxt_model, training_duration=12.3)

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            model_reloaded = model_repo.get_by_id(fxt_model.id_)
        assert model_reloaded.training_duration == 12.3

    def test_update_training_job_duration(self, request, fxt_empty_project, fxt_model_storage, fxt_model) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save(fxt_model)

        model_repo.update_training_job_duration(model=fxt_model, training_job_duration=12.3)

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            model_reloaded = model_repo.get_by_id(fxt_model.id_)
        assert model_reloaded.training_job_duration == 12.3

    def test_delete_by_id(
        self, request, fxt_empty_project, fxt_model_storage, fxt_model_success, fxt_model_failed
    ) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save_many([fxt_model_success, fxt_model_failed])

        model_repo.delete_by_id(fxt_model_success.id_)

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
        ):
            assert isinstance(model_repo.get_by_id(fxt_model_success.id_), NullModel)
            assert not isinstance(model_repo.get_by_id(fxt_model_failed.id_), NullModel)

    def test_delete_all(self, request, fxt_model_storage, fxt_model_success, fxt_model_failed) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save_many([fxt_model_success, fxt_model_failed])

        model_repo.delete_all()

        assert not list(model_repo.get_all())

    def test_set_purge_info(self, request, fxt_model_storage, fxt_model) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save(fxt_model)
        fxt_model.purge_info.is_purged = True
        model_repo.set_purge_info(fxt_model)
        new_model = model_repo.get_by_id(fxt_model.id_)
        assert new_model.purge_info.is_purged == fxt_model.purge_info.is_purged

    def test_get_non_purged_base_models(self, request, fxt_model_storage, fxt_model_success, fxt_model_failed) -> None:
        model_repo = ModelRepo(fxt_model_storage.identifier)
        fxt_model_success.model_format = ModelFormat.BASE_FRAMEWORK
        fxt_model_failed.model_format = ModelFormat.BASE_FRAMEWORK
        request.addfinalizer(lambda: model_repo.delete_all())
        model_repo.save_many([fxt_model_success, fxt_model_failed])
        base_models = model_repo.get_non_purged_base_models()
        assert fxt_model_success in base_models
        assert fxt_model_failed not in base_models
