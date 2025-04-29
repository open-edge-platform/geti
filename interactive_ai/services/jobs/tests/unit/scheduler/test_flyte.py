# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import deepcopy
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call, patch

import pytest
from bson import ObjectId
from flytekit import Annotations, Labels
from flytekit.exceptions.user import FlyteEntityNotExistException
from flytekit.models.core.workflow import NodeMetadata
from flytekit.models.filters import ValueIn
from flytekit.remote import FlyteLaunchPlan, FlyteNode, FlyteTask, FlyteWorkflow, FlyteWorkflowExecution
from flytekit.remote.entities import FlyteBranchNode
from flytekit.tools.translator import Options

from model.telemetry import Telemetry
from scheduler.flyte import ExecutionType, Flyte

from geti_types import ID, make_session

if TYPE_CHECKING:
    from flytekit.models.execution import Execution

ORGANIZATION_ID = str(ObjectId())


def mock_flyte_client(self, *args, **kwargs) -> None:
    self.client = MagicMock()
    self.client.client = MagicMock()


def reset_singletons() -> None:
    Flyte._instance = None  # type: ignore[attr-defined]


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_fetch_workflow(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange

    # Act
    Flyte().fetch_workflow(
        workflow_name="workflow_name",
        workflow_version="workflow_version",
    )

    # Assert
    Flyte().client.fetch_workflow.assert_called_once_with(name="workflow_name", version="workflow_version")


@pytest.mark.parametrize(
    "workspace_id, project_id, execution_type, values",
    [
        (
            "workspace",
            None,
            ExecutionType.MAIN,
            {
                "workspace_id": "workspace",
                "execution_type": "MAIN",
                "opentelemetry_context": "context",
                "organization_id": ORGANIZATION_ID,
                "report_resources_consumption": "true",
            },
        ),
        (
            "workspace",
            "project",
            ExecutionType.MAIN,
            {
                "workspace_id": "workspace",
                "project_id": "project",
                "execution_type": "MAIN",
                "opentelemetry_context": "context",
                "organization_id": ORGANIZATION_ID,
                "report_resources_consumption": "true",
            },
        ),
        (
            "workspace",
            None,
            ExecutionType.REVERT,
            {
                "workspace_id": "workspace",
                "execution_type": "REVERT",
                "opentelemetry_context": "context",
                "organization_id": ORGANIZATION_ID,
                "report_resources_consumption": "true",
            },
        ),
        (
            "workspace",
            "project",
            ExecutionType.REVERT,
            {
                "workspace_id": "workspace",
                "project_id": "project",
                "execution_type": "REVERT",
                "opentelemetry_context": "context",
                "organization_id": ORGANIZATION_ID,
                "report_resources_consumption": "true",
            },
        ),
    ],
)
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_workflow_execution(request, workspace_id, project_id, execution_type, values, fxt_job) -> None:
    values["job_id"] = fxt_job.id

    annotations = deepcopy(values)
    annotations["job_type"] = fxt_job.type
    annotations["job_name"] = fxt_job.job_name
    annotations["job_author"] = str(fxt_job.author)
    annotations["job_start_time"] = fxt_job.start_time.isoformat()
    request.addfinalizer(reset_singletons)

    # Arrange
    workflow: FlyteWorkflow = MagicMock()

    # Act
    Flyte().start_workflow_execution(
        workspace_id=workspace_id,
        job=fxt_job,
        project_id=project_id,
        execution_type=execution_type,
        execution_name="execution_name",
        workflow=workflow,
        payload={"a": 1, "b": 2, "c": 3, "d": 4},
        telemetry=Telemetry(context=values["opentelemetry_context"]),
        session=make_session(
            organization_id=ID(ORGANIZATION_ID),
        ),
    )

    # Assert
    Flyte().client.execute_remote_wf.assert_called_once_with(
        entity=workflow,
        execution_name="execution_name",
        wait=False,
        inputs={"a": 1, "b": 2, "c": 3, "d": 4},
        options=Options(
            labels=Labels(values),
            annotations=Annotations(annotations),
        ),
    )


@pytest.mark.parametrize(
    "execution_type, result",
    [
        ("MAIN", ExecutionType.MAIN),
        ("REVERT", ExecutionType.REVERT),
    ],
)
def test_get_execution_type(execution_type, result) -> None:
    # Arrange
    execution: FlyteWorkflowExecution = MagicMock()
    execution.spec.annotations.values = {"execution_type": execution_type}

    # Act
    execution_type = Flyte.get_execution_type(execution)

    # Assert
    assert execution_type == result


def test_get_execution_workspace_id() -> None:
    # Arrange
    execution: FlyteWorkflowExecution = MagicMock()
    execution.spec.annotations.values = {"workspace_id": "workspace"}

    # Act
    workspace_id = Flyte.get_execution_workspace_id(execution)

    # Assert
    assert workspace_id == "workspace"


def test_get_execution_job_id() -> None:
    # Arrange
    execution: FlyteWorkflowExecution = MagicMock()
    execution.spec.annotations.values = {"job_id": "job"}

    # Act
    job_id = Flyte.get_execution_job_id(execution)

    # Assert
    assert job_id == "job"


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_cancel_workflow_execution(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution: FlyteWorkflowExecution = MagicMock()

    # Act
    Flyte().cancel_workflow_execution(execution=execution)

    # Assert
    Flyte().client.terminate.assert_called_once_with(execution=execution, cause="Canceling execution")


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_fetch_execution_not_found(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    Flyte().client.fetch_execution.side_effect = FlyteEntityNotExistException()

    # Act
    found_execution = Flyte().fetch_workflow_execution(execution_name="execution_name")

    # Assert
    Flyte().client.fetch_execution.assert_called_once_with(name="execution_name")
    assert found_execution is None


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_fetch_execution_found(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution: Execution = MagicMock()
    Flyte().client.fetch_execution.return_value = execution

    # Act
    found_execution = Flyte().fetch_workflow_execution(execution_name="execution_name")

    # Assert
    Flyte().client.fetch_execution.assert_called_once_with(name="execution_name")
    Flyte().client.sync_execution.assert_not_called()
    assert found_execution == execution


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_list_workflow_executions_empty_list(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    client = MagicMock()
    Flyte().client.client = client

    # Act
    executions = Flyte().list_workflow_executions(execution_names=[])

    # Assert
    client.list_executions_paginated.assert_not_called()
    assert executions == []


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_list_workflow_executions(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution = MagicMock()
    client = MagicMock()
    Flyte().client.client = client
    client.list_executions_paginated.return_value = ([execution], "")

    # Act
    executions = Flyte().list_workflow_executions(execution_names=["execution_name"])

    # Assert
    client.list_executions_paginated.assert_called_once_with(
        project="impt-jobs",
        domain="production",
        filters=[ValueIn(key="execution_name", values=["execution_name"])],
    )
    assert len(executions) == 1
    assert executions[0].id == execution.id


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_fetch_task_not_found(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    Flyte().client.fetch_task.side_effect = FlyteEntityNotExistException()

    # Act
    found_execution = Flyte().fetch_task(name="step_name", version="task_version")

    # Assert
    Flyte().client.fetch_task.assert_called_once_with(
        project="impt-jobs",
        domain="production",
        name="step_name",
        version="task_version",
    )
    assert found_execution is None


@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_fetch_task_found(request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    task: FlyteTask = MagicMock()
    Flyte().client.fetch_task.return_value = task

    # Act
    found_task = Flyte().fetch_task(name="step_name", version="task_version")

    # Assert
    Flyte().client.fetch_task.assert_called_once_with(
        project="impt-jobs",
        domain="production",
        name="step_name",
        version="task_version",
    )
    assert found_task == task


@patch("scheduler.flyte.Flyte.get_node_branch_nodes")
def test_get_workflow_branch_nodes(mock_get_node_branch_nodes) -> None:
    # Arrange
    workflow: FlyteWorkflow = MagicMock()
    node1: FlyteNode = MagicMock()
    node2: FlyteNode = MagicMock()

    workflow.flyte_nodes = [node1, node2]

    mock_get_node_branch_nodes.side_effect = [{"n1": node1}, {"n2": node2}]

    # Act
    branch_nodes = Flyte.get_workflow_branch_nodes(workflow=workflow)

    # Assert
    mock_get_node_branch_nodes.assert_has_calls(
        [call(node=node1)],
        [call(node=node2)],
    )
    assert branch_nodes == {"n1": node1, "n2": node2}


def test_get_node_branch_nodes_task_node() -> None:
    # Arrange
    node: FlyteNode = MagicMock()
    task: FlyteTask = MagicMock(spec=FlyteTask)

    node.flyte_entity = task

    # Act
    branch_nodes = Flyte.get_node_branch_nodes(node=node)

    # Assert
    assert branch_nodes == {}


@patch("scheduler.flyte.Flyte.get_workflow_branch_nodes")
def test_get_node_branch_nodes_workflow_node(mock_get_workflow_branch_nodes) -> None:
    # Arrange
    node: FlyteNode = MagicMock()
    workflow: FlyteWorkflow = MagicMock(spec=FlyteWorkflow)

    node.flyte_entity = workflow

    branch_node: FlyteNode = MagicMock()
    mock_get_workflow_branch_nodes.return_value = {"n0": branch_node}

    # Act
    branch_nodes = Flyte.get_node_branch_nodes(node=node)

    # Assert
    mock_get_workflow_branch_nodes.assert_called_once_with(workflow=workflow)
    assert branch_nodes == {"n0": branch_node}


def test_get_node_branch_nodes_launch_plan_node_none_workflow() -> None:
    # Arrange
    node: FlyteNode = MagicMock()
    launch_plan: FlyteLaunchPlan = MagicMock(spec=FlyteLaunchPlan)
    launch_plan.flyte_workflow = None

    node.flyte_entity = launch_plan

    # Act
    branch_nodes = Flyte.get_node_branch_nodes(node=node)

    # Assert
    assert branch_nodes == {}


@patch("scheduler.flyte.Flyte.get_workflow_branch_nodes")
def test_get_node_branch_nodes_launch_plan_node_workflow(
    mock_get_workflow_branch_nodes,
) -> None:
    # Arrange
    node: FlyteNode = MagicMock()
    launch_plan: FlyteTask = MagicMock(spec=FlyteLaunchPlan)
    workflow: FlyteWorkflow = MagicMock(spec=FlyteWorkflow)
    launch_plan.flyte_workflow = workflow

    node.flyte_entity = launch_plan

    branch_node: FlyteNode = MagicMock()
    mock_get_workflow_branch_nodes.return_value = {"n0": branch_node}

    # Act
    branch_nodes = Flyte.get_node_branch_nodes(node=node)

    # Assert
    mock_get_workflow_branch_nodes.assert_called_once_with(workflow=workflow)
    assert branch_nodes == {"n0": branch_node}


def test_get_node_branch_nodes_branch_node() -> None:
    # Arrange
    flyte_node: FlyteNode = MagicMock()
    flyte_node.metadata = NodeMetadata("condition")
    branch_node: FlyteBranchNode = MagicMock(spec=FlyteBranchNode)

    then_node: FlyteNode = MagicMock()
    then_node.metadata = NodeMetadata("then")
    branch_node.if_else.case.then_node = then_node

    else_node: FlyteNode = MagicMock()
    else_node.metadata = NodeMetadata("else")
    branch_node.if_else.else_node = else_node

    flyte_node.flyte_entity = branch_node

    original_get_node_branch_nodes = Flyte.get_node_branch_nodes
    with patch("scheduler.flyte.Flyte.get_node_branch_nodes") as mock_get_node_branch_nodes:

        def side_effect(node):
            if node == flyte_node:
                return original_get_node_branch_nodes(node=node)
            return {}

        mock_get_node_branch_nodes.side_effect = side_effect

        # Act
        branch_nodes = Flyte.get_node_branch_nodes(node=flyte_node)

        # Assert
        mock_get_node_branch_nodes.assert_has_calls(
            [
                call(node=flyte_node),
                call(node=then_node),
                call(node=else_node),
            ],
        )
        assert branch_nodes == {
            "then": flyte_node,
            "else": flyte_node,
        }
