# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from iai_core.adapters.model_adapter import ExportableCodeAdapter
from iai_core.entities.datasets import NullDataset
from iai_core.entities.model import Model, ModelFormat, ModelStatus
from iai_core.repos import ModelRepo
from iai_core.repos.metrics_reporting_model_storage_repo import MetricsReportingModelStorageRepo
from iai_core.services import ModelService
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.project_factory import ProjectFactory
from tests.test_helpers import empty_model_configuration


class TestMetricsReportingModelStorageRepo:
    def test_total_models_per_arch_and_type(
        self,
        request,
        fxt_model_template_classification,
        fxt_model_template_detection,
        fxt_training_framework,
    ) -> None:
        """
        <b>Description:</b>
        Check that the total models count is correct

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The model repository returns appropriate count value

        <b>Steps</b>
        1. Check current totals
        1. Create projects with a trained model
        2. Assert number of models is equal to the current totals plus created models
        """
        metrics_repo = MetricsReportingModelStorageRepo()

        current_totals_arch = metrics_repo.get_total_number_of_models_per_arch()
        classification_model = "Mock/Classification"
        detection_model = "Mock/Detection"
        current_classification_model = current_totals_arch.get(classification_model, 0)
        current_detection_model = current_totals_arch.get(detection_model, 0)

        current_totals_type = metrics_repo.get_total_number_of_models_per_task_type()
        classification = "CLASSIFICATION"
        detection = "DETECTION"
        current_classification = current_totals_type.get(classification, 0)
        current_detection = current_totals_type.get(detection, 0)

        num_projects = 4
        for i in range(num_projects):
            model_template_id = fxt_model_template_classification if i > 0 else fxt_model_template_detection
            project = ProjectFactory.create_project_single_task(
                name=f"test_project_{i}",
                creator_id="",
                description="",
                labels=[
                    {"name": "a", "color": "#00ff00ff"},
                ],
                model_template_id=model_template_id,
            )
            task_node = project.get_trainable_task_nodes()[0]
            model_storage = ModelService.get_active_model_storage(
                project_identifier=project.identifier, task_node_id=task_node.id_
            )
            model_repo = ModelRepo(model_storage.identifier)
            model = Model(
                project=project,
                model_storage=model_storage,
                train_dataset=NullDataset(),
                configuration=empty_model_configuration(),
                id_=model_repo.generate_id(),
                data_source_dict={"inference_model.bin": b"weights_data"},
                training_framework=fxt_training_framework,
                model_status=ModelStatus.SUCCESS,
                model_format=ModelFormat.BASE_FRAMEWORK,
                exportable_code_adapter=ExportableCodeAdapter(data_source=b"exportable_code"),
            )
            model_repo.save(model)
            request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        new_totals_arch = metrics_repo.get_total_number_of_models_per_arch()
        new_classification_model = new_totals_arch.get(classification_model, 0)
        new_detection_model = new_totals_arch.get(detection_model, 0)

        new_totals_type = metrics_repo.get_total_number_of_models_per_task_type()
        new_classification = new_totals_type.get(classification, 0)
        new_detection = new_totals_type.get(detection, 0)

        assert new_detection_model == current_detection_model + 1
        assert new_classification_model == current_classification_model + 3
        assert new_detection == current_detection + 1
        assert new_classification == current_classification + 3
