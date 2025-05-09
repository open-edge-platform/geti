# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from iai_core.repos.metrics_reporting_project_repo import MetricsReportingProjectRepo
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.project_factory import ProjectFactory


class TestMetricsReportingProjectRepo:
    def test_count_all_projects(
        self,
        request,
        fxt_model_template_classification,
        fxt_model_template_detection,
    ) -> None:
        """
        <b>Description:</b>
        Check that the project count is correct

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The project repository returns appropriate count value

        <b>Steps</b>
        1. Assert no projects are present in the repository
        1. Create projects
        2. Assert number of projects is equal to count_all
        """
        metrics_repo = MetricsReportingProjectRepo()

        current_totals = metrics_repo.get_total_number_of_projects_per_project_type()
        classification = "CLASSIFICATION"
        detection = "DETECTION"
        current_classification = current_totals.get(classification, 0)
        current_detection = current_totals.get(detection, 0)

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
            request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        new_totals = metrics_repo.get_total_number_of_projects_per_project_type()
        new_classification = new_totals.get(classification, 0)
        new_detection = new_totals.get(detection, 0)

        assert new_detection == current_detection + 1
        assert new_classification == current_classification + 3
