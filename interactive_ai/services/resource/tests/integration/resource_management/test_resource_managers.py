# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io
from unittest.mock import patch

import cv2
import pytest
from _pytest.fixtures import FixtureRequest
from geti_spicedb_tools import SpiceDB
from tests.utils.custom_project_parser import CustomTestProjectParser

from communication.rest_parsers import RestProjectParser, RestProjectUpdateParser
from communication.rest_views.project_rest_views import ProjectRESTViews
from managers.annotation_manager import AnnotationManager
from managers.project_manager import ProjectManager
from resource_management.media_manager import MediaManager
from service.label_schema_service import LabelSchemaService

from geti_types import CTX_SESSION_VAR, ID, ImageIdentifier
from iai_core.adapters.binary_interpreters import RAWBinaryInterpreter
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core.entities.label_schema import LabelSchemaView, NullLabelSchema
from iai_core.entities.media import ImageExtensions, VideoExtensions
from iai_core.repos import AnnotationSceneRepo, ImageRepo, LabelRepo, LabelSchemaRepo, ProjectRepo, VideoRepo
from iai_core.repos.storage.storage_client import BytesStream
from iai_core.utils.project_builder import PersistedProjectBuilder, ProjectBuilder


@pytest.fixture(scope="function")
def fxt_pipeline_data_single_classification_task(request: FixtureRequest):
    """
    Defines a Pipeline with two tasks:
     - 2D media dataset
     - Classification task
    It defines three labels:
     - Bird (in exclusive group `bird`)
     - Woodpecker (in exclusive group `bird`, child of label `Bird`)
     - Mammal (In exclusive group `vertebrates`)
    """
    yield {
        "connections": [{"from": "Dataset", "to": "Classification task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "task_type": "classification",
                "title": "Classification task",
                "labels": [
                    {
                        "name": "Bird",
                        "color": "#ffffff",
                        "group": "birds",
                        "hotkey": "crtl+0",
                    },
                    {
                        "name": "Woodpecker",
                        "color": "#ffffee",
                        "group": "birds",
                        "hotkey": "crtl+1",
                    },
                    {
                        "name": "Mammal",
                        "color": "#ffffdd",
                        "group": "vertebrates",
                        "hotkey": "crtl+2",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_create_upload_annotate_project(
    fxt_pipeline_data_single_classification_task,
    fxt_random_annotated_video_factory,
    fxt_random_annotated_image_factory,
):
    """
    Create a random project through the resource MS. This is different from making it
    through the repo's, As this simulates uploads as well
    """
    workspace_id = CTX_SESSION_VAR.get().workspace_id
    project_manager = ProjectManager()
    media_manager = MediaManager()
    annotation_manager = AnnotationManager()

    model_template_dataset = ModelTemplateList().get_by_id("dataset")
    model_template_classification = ModelTemplateList().get_by_id("classification")

    with (
        patch.object(SpiceDB, "create_project"),
        patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                model_template_dataset,
                model_template_classification,
            ],
        ),
    ):
        project_data = {
            "name": "Test create, upload and annotate",
            "pipeline": fxt_pipeline_data_single_classification_task,
        }
        project, _, _ = project_manager.create_project(
            creator_id="admin",
            workspace_id=workspace_id,
            project_parser=RestProjectParser,
            parser_kwargs={"rest_data": project_data},
        )
    project_label_schema = LabelSchemaRepo(project.identifier).get_latest()
    labels = project_label_schema.get_labels(include_empty=False)
    dataset_storage = project.get_training_dataset_storage()

    annotations_to_save: list[AnnotationScene] = []
    for i in range(1, 16):
        img_basename = f"image {i}"

        image1, _ = fxt_random_annotated_image_factory(image_width=512, image_height=384, labels=labels)

        # Make jpeg out of numpy data, and `upload` it
        is_success, buffer = cv2.imencode(".jpg", image1, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        image = media_manager.upload_image(
            dataset_storage_identifier=dataset_storage.identifier,
            basename=img_basename,
            extension=ImageExtensions.JPG,
            data_stream=BytesStream(data=io.BytesIO(buffer), length=len(buffer)),
            user_id=ID("dummy_user"),
        )
        identifier = ImageIdentifier(image.id_)

        # Re-create annotation, and `upload` it. Simulates a user pressing save
        annotations_to_save.append(
            AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=identifier,
                media_height=image.height,
                media_width=image.width,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=[],
            )
        )
    annotation_manager.save_annotations(
        annotation_scenes=annotations_to_save,
        project=project,
        dataset_storage_identifier=dataset_storage.identifier,
        label_schema=project_label_schema,
        calculate_task_to_revisit=False,
    )

    # test applying label hierarchy at upload video
    video, _, _, _, _, _, _ = fxt_random_annotated_video_factory(project=project, number_of_frames=60)

    video_repo: VideoRepo = VideoRepo(dataset_storage.identifier)
    video_data = video_repo.binary_repo.get_by_filename(
        filename=video.data_binary_filename, binary_interpreter=RAWBinaryInterpreter()
    )
    video = media_manager.upload_video(
        dataset_storage_identifier=dataset_storage.identifier,
        basename="Test video",
        extension=VideoExtensions.MP4,
        data_stream=BytesStream(data=io.BytesIO(video_data), length=len(video_data)),
        user_id=ID("dummy_user"),
    )
    ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
    annotations = ann_scene_repo.get_latest_annotations_by_kind_and_media_id(
        media_id=video.media_identifier.media_id,
        annotation_kind=AnnotationSceneKind.ANNOTATION,
    )
    yield project, annotations


@pytest.fixture
def fxt_anomaly_classification_project_data():
    yield {
        "name": "Test anomaly classification project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Anomaly task": {
                "task_type": "anomaly_classification",
            },
        },
    }


@pytest.fixture
def fxt_hierarchy_classification_project_data_2():
    yield {
        "name": "Test hierarchy classification project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Classification task": {
                "task_type": "classification",
                "labels": {
                    "1": {
                        "color": "#edb200ff",
                        "group": "Group 1",
                        "parent_id": None,
                        "hotkey": "",
                    },
                    "1.1": {
                        "color": "#548fadff",
                        "group": "Group 1.X",
                        "parent_id": "1",
                        "hotkey": "",
                    },
                    "1.1.1": {
                        "color": "#00f5d4ff",
                        "group": "Group 1.1.X",
                        "parent_id": "1.1",
                        "hotkey": "",
                    },
                    "1.1.2": {
                        "color": "#5b69ffff",
                        "group": "Group 1.1.X",
                        "parent_id": "1.1",
                        "hotkey": "",
                    },
                    "1.2": {
                        "color": "#9d3b1aff",
                        "group": "Group 1.X",
                        "parent_id": "1",
                        "hotkey": "",
                    },
                    "1.3": {
                        "color": "#d7bc5eff",
                        "group": "Group 1.X",
                        "parent_id": "1",
                        "hotkey": "",
                    },
                    "2": {
                        "color": "#708541ff",
                        "group": "Group 2",
                        "parent_id": None,
                        "hotkey": "",
                    },
                    "2.1": {
                        "color": "#c9e649ff",
                        "group": "Group 2.X",
                        "parent_id": "2",
                        "hotkey": "",
                    },
                },
            },
        },
    }


class TestResourceManagers:
    def test_create_delete_project(self, fxt_create_upload_annotate_project) -> None:
        """
        <b>Description:</b>
        To test the create and delete project functionalities of the resource ms.

        <b>Input data:</b>
        A project with some annotations.

        <b>Expected results:</b>
        Test passes if project creation and deletion are executed successfully.

        <b>Steps</b>
        1. Create a new project via the resource ms.
        2. Check if the created project is the same as the input project.
        3. Check that all the get_all_by_project_id functions work for the created project.
        4. Delete the project via the resource ms.
        5. Check that the project no longer exists
        """
        # Create a project and some annotations
        project_input, annotations_input = fxt_create_upload_annotate_project

        # Test correctness of label schema
        label_schema = LabelSchemaRepo(project_input.identifier).get_latest()
        assert len(label_schema.get_groups(include_empty=True)) == 2, (
            "Expected two EXCLUSIVE label groups in the label schema"
        )

        for group in label_schema.get_groups(include_empty=True):
            if group.name == "birds":
                label_names_in_group = [label.name for label in group.labels]
                assert len(label_names_in_group) == 2, "Expected two labels in group `birds`"
                assert "Bird" in label_names_in_group, "Expected label `Bird` in group `birds`"
                assert "Woodpecker" in label_names_in_group, "Expected label `Woodpecker` in group `birds`"
            elif group.name == "vertebrates":
                label_names_in_group = [label.name for label in group.labels]
                assert len(label_names_in_group) == 1, "Expected one label in group `vertebrates`"
                assert "Mammal" in label_names_in_group, "Expected label `Mammal` in group `vertebrates`"
            elif group.name == "No class":
                assert len(group.labels) == 1, "Expected a single label in the empty label group"
            else:
                raise ValueError(f"Unexpected label group {group.name}")

        # Check that the created project matches the input project
        project_repo = ProjectRepo()
        project_input_label_schema = LabelSchemaRepo(project_input.identifier).get_latest()
        project_created = project_repo.get_by_id(project_input.id_)
        project_created_label_schema = LabelSchemaRepo(project_created.identifier).get_latest()
        dataset_storage_created = project_created.get_training_dataset_storage()

        assert project_input.id_ == project_created.id_, (
            "The project id differed after fetching the project from the repo again"
        )
        assert project_input.name == project_created.name, (
            "The project name differed after fetching the project from the repo again"
        )
        assert project_input.description == project_created.description, (
            "The project description differed after fetching the project from the repo again"
        )

        assert len(project_input_label_schema.get_labels(True)) == len(project_created_label_schema.get_labels(True)), (
            "The number of labels differed after fetching the project from the repo again"
        )

        assert len(project_input.task_graph.tasks) == len(project_created.task_graph.tasks), (
            "The number of task nodes differed after fetching the project from the repo again"
        )

        assert project_input.task_graph.ordered_tasks == project_created.task_graph.ordered_tasks, (
            "The task nodes differed after fetching the project from the repo again"
        )

        # Check that get_all_by_project_id functions work.
        task_nodes_created = project_created.tasks
        ann_scene_repo = AnnotationSceneRepo(dataset_storage_created.identifier)
        annotations_created = list(ann_scene_repo.get_all())
        image_repo = ImageRepo(dataset_storage_created.identifier)
        video_repo = VideoRepo(dataset_storage_created.identifier)
        images_created = list(image_repo.get_all())
        videos_created = list(video_repo.get_all())

        assert len(annotations_created) > 0, "Expected multiple annotations"
        assert len(project_input.tasks) == len(task_nodes_created), "Expected multiple task nodes"
        assert len(images_created) > 0, "Expected multiple images"
        assert len(videos_created) > 0, "Expected multiple videos"

        # Try to delete an image
        images_before = len(images_created)
        MediaManager().delete_image_by_id(
            project=project_created,
            dataset_storage=dataset_storage_created,
            image_id=images_created[0].id_,
        )
        images_after = len(list(image_repo.get_all()))
        assert images_after == images_before - 1

        # Try to delete a video
        videos_before = len(videos_created)
        MediaManager().delete_video_by_id(
            project=project_created,
            dataset_storage=dataset_storage_created,
            video_id=videos_created[0].id_,
        )
        videos_after = len(list(video_repo.get_all()))
        assert videos_after == videos_before - 1

        # Try to delete the project
        with patch.object(SpiceDB, "delete_project"):
            ProjectManager.delete_project(project_id=project_created.id_)

        # Checking that there are no more projects
        all_projects_in_workspace = list(ProjectRepo().get_all())
        assert len(all_projects_in_workspace) == 0, "Expected the project to be deleted"

    @pytest.mark.parametrize(
        "lazyfxt_project_request, model_template_id",
        [
            ("fxt_hierarchy_classification_project_data_2", "classification"),
        ],
    )
    def test_update_project(
        self,
        lazyfxt_project_request,
        model_template_id,
        request: FixtureRequest,
    ) -> None:
        """
        <b>Description:</b>
        Tests the resource manager's ability to update the name of a project and a label's name and color.

        <b>Input data:</b>
        An annotated project.

        <b>Expected results:</b>
        Test passes if the project is updated correctly.

        <b>Steps</b>
        1. Generate a project.
        2. Update the project name and one label's color and name using update_project.
        3. Fetch the label and project from the repo and check that they are updated.
        4. Update only the project name using update_project
        5. Check that the name is updated and the labels are unchanged
        6. Update only a label's color and not it's name or the project name using update_project
        7. Check that the label's color is updated and it's name and project_name are unchanged
        """
        project_type = request.getfixturevalue(lazyfxt_project_request)
        session = CTX_SESSION_VAR.get()
        project_manager = ProjectManager()
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id(model_template_id),
            ],
        ):
            project, label_schema, task_schema = PersistedProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=project_type,
            )
        label_repo = LabelRepo(project.identifier)
        label_schema_per_task: dict[ID, LabelSchemaView | NullLabelSchema] = {
            task_node.id_: (
                LabelSchemaService.get_latest_label_schema_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task_node.id_,
                )
                if task_node.task_properties.is_trainable
                else NullLabelSchema()
            )
            for task_node in project.task_graph.tasks
        }

        # update name and one label
        pipeline_rest = ProjectRESTViews.project_to_rest(
            organization_id=session.organization_id,
            project=project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )["pipeline"]
        id_of_label_to_be_updated = pipeline_rest["tasks"][-1]["labels"][1]["id"]
        first_updated_project_name = "updated project name 1"
        first_updated_label_name = "updated label name 1"
        first_updated_label_color = "#0016ffff"
        pipeline_rest["tasks"][-1]["labels"][1]["name"] = first_updated_label_name
        pipeline_rest["tasks"][-1]["labels"][1]["color"] = first_updated_label_color

        data = {
            "id": project.id_,
            "name": first_updated_project_name,
            "pipeline": pipeline_rest,
        }
        project_manager.update_project(
            project=project,
            project_update_parser=RestProjectUpdateParser,
            parser_kwargs={"rest_data": data},
        )

        first_updated_project = ProjectRepo().get_by_id(project.id_)
        first_updated_label = label_repo.get_by_id(id_of_label_to_be_updated)
        assert first_updated_project.name == first_updated_project_name
        assert first_updated_label.color.hex_str == first_updated_label_color
        assert first_updated_label.name == first_updated_label_name

        # update only the name
        pre_update_pipeline = ProjectRESTViews.project_to_rest(
            organization_id=session.organization_id,
            project=first_updated_project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )["pipeline"]
        second_updated_project_name = "updated project name 2"
        data = {
            "id": project.id_,
            "name": second_updated_project_name,
            "pipeline": pre_update_pipeline,
        }
        project_manager.update_project(
            project=project,
            project_update_parser=RestProjectUpdateParser,
            parser_kwargs={"rest_data": data},
        )

        second_updated_project = ProjectRepo().get_by_id(project.id_)
        post_update_pipeline = ProjectRESTViews.project_to_rest(
            organization_id=session.organization_id,
            project=second_updated_project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )["pipeline"]
        assert second_updated_project.name == second_updated_project_name
        assert pre_update_pipeline == post_update_pipeline

        # update only a label color
        pipeline_rest = ProjectRESTViews.project_to_rest(
            organization_id=session.organization_id,
            project=second_updated_project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )["pipeline"]
        id_of_label_to_be_updated = pipeline_rest["tasks"][-1]["labels"][1]["id"]
        pre_update_project_name = second_updated_project.name
        pre_update_label_name = label_repo.get_by_id(id_of_label_to_be_updated).name
        third_updated_label_color = "#15ff00ff"
        pipeline_rest["tasks"][-1]["labels"][1]["color"] = third_updated_label_color
        data = {
            "id": project.id_,
            "name": pre_update_project_name,
            "pipeline": pipeline_rest,
        }
        _, _, task_schema = project_manager.update_project(
            project=project,
            project_update_parser=RestProjectUpdateParser,
            parser_kwargs={"rest_data": data},
        )
        third_updated_project = ProjectRepo().get_by_id(project.id_)
        third_updated_label = label_repo.get_by_id(id_of_label_to_be_updated)
        assert third_updated_project.name == pre_update_project_name
        assert third_updated_label.color.hex_str == third_updated_label_color
        assert third_updated_label.name == pre_update_label_name

    def test_update_project_anomaly(self, fxt_anomaly_classification_project_data) -> None:
        model_template_id = "anomaly_classification"
        project_type = fxt_anomaly_classification_project_data
        session = CTX_SESSION_VAR.get()
        project_manager = ProjectManager()
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                ModelTemplateList().get_by_id("dataset"),
                ModelTemplateList().get_by_id(model_template_id),
            ],
        ):
            project, label_schema, task_schema = PersistedProjectBuilder.build_full_project(
                creator_id="Geti",
                parser_class=CustomTestProjectParser,
                parser_kwargs=project_type,
            )
        label_schema_per_task: dict[ID, LabelSchemaView | NullLabelSchema] = {
            task_node.id_: (
                LabelSchemaService.get_latest_label_schema_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task_node.id_,
                )
                if task_node.task_properties.is_trainable
                else NullLabelSchema()
            )
            for task_node in project.task_graph.tasks
        }

        # update name and one label
        pipeline_rest = ProjectRESTViews.project_to_rest(
            organization_id=session.organization_id,
            project=project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )["pipeline"]

        new_project_name = "New Anomaly project name"
        data = {
            "id": project.id_,
            "name": new_project_name,
            "pipeline": pipeline_rest,
        }
        project_manager.update_project(
            project=project,
            project_update_parser=RestProjectUpdateParser,
            parser_kwargs={"rest_data": data},
        )

        first_updated_project = ProjectRepo().get_by_id(project.id_)
        assert first_updated_project.name == new_project_name
