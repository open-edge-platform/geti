from behave import then, when
from geti_client import TriggerModelTestJobRequest


@when("the user requests to test the model on the default dataset")
def step_user_requests_model_test(context):
    model_group = context.models_api.get_model_groups(
        organization_id=context.organization_id, workspace_id=context.workspace_id, project_id=context.project_id
    ).model_groups[0]
    model_group_id = model_group.id
    base_model_id = model_group.models[0].id
    optimized_models = context.models_api.get_model_detail(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        model_group_id=model_group_id,
        model_id=base_model_id,
    ).optimized_models
    for optimized_model in optimized_models:
        if "FP16" in optimized_model.precision:
            optimized_model_id = optimized_model.id
            break
    else:
        raise RuntimeError("No FP16 optimized model found in the model group")

    trigger_model_test = TriggerModelTestJobRequest(
        name="Test 1", dataset_ids=[context.dataset_id], model_group_id=model_group_id, model_id=optimized_model_id
    )
    model_test_response = context.tests_api.trigger_model_test_job(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        project_id=context.project_id,
        trigger_model_test_job_request=trigger_model_test,
    )
    context.job_id = model_test_response.job_id


@then("a model test report is created")
def step_a_model_test_report_is_created(context):
    model_test_results = context.tests_api.get_all_tests_in_a_project(
        organization_id=context.organization_id, workspace_id=context.workspace_id, project_id=context.project_id
    ).test_results
    assert len(model_test_results) == 1, "Expected one model test report to be created"


@then("the model test report has a non-null score")
def step_the_model_test_report_has_non_null_score(context):
    model_test_result = context.tests_api.get_all_tests_in_a_project(
        organization_id=context.organization_id, workspace_id=context.workspace_id, project_id=context.project_id
    ).test_results[0]
    assert model_test_result.scores[0].value > 0, "Expected a model test score greater than 0"


@then("the model test report has a number of media greater than 0")
def step_the_model_test_report_has_more_than_0_media(context):
    model_test_result = context.tests_api.get_all_tests_in_a_project(
        organization_id=context.organization_id, workspace_id=context.workspace_id, project_id=context.project_id
    ).test_results[0]
    assert model_test_result.datasets_info[0].n_samples > 0, "Expected more than 0 samples in the dataset "
