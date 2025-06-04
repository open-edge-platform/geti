from behave import step, when
from geti_client import TestsApi, TriggerModelTestJobRequest


@when("the user requests to test the model on dataset 'Test'")
def step_user_requests_model_test(context):
    trigger_model_test_job_request = TriggerModelTestJobRequest(dataset_ids=[context.dataset.id])
    TestsApi.trigger_model_test_job(
        organization_id=context.organization.id,
        workspace_id=context.workspace.id,
        project_id=context.project.id,
        trigger_model_test_job_request=trigger_model_test_job_request,
    )


@step("a model test report is created")
def step_a_model_test_report_is_created(context):
    model_test_results = TestsApi.get_all_tests_in_a_project(
        organization_id=context.organization.id, workspace_id=context.workspace.id, project_id=context.project.id
    ).test_results
    assert len(model_test_results) == 1, "Expected one model test report to be created"


@step("the model test report has a non-null score")
def step_the_model_test_report_has_non_null_score(context):
    model_test_result = TestsApi.get_all_tests_in_a_project(
        organization_id=context.organization.id, workspace_id=context.workspace.id, project_id=context.project.id
    ).test_results[0]
    assert model_test_result.scores[0].value > 0, "Expected a model test score greater than 0"


@step("the model test report has a number of media greater than 0")
def step_the_model_test_report_has_more_than_0_media(context):
    model_test_result = TestsApi.get_all_tests_in_a_project(
        organization_id=context.organization.id, workspace_id=context.workspace.id, project_id=context.project.id
    ).test_results[0]
    assert model_test_result.datasets_info[0].n_samples > 0, "Expected more than 0 samples in the dataset "
