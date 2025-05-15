#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#
import time

import pytest
from testfixtures import compare

from iai_core.adapters.adapter import ReferenceAdapter
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.project import Project
from iai_core.repos import DatasetStorageRepo, ProjectRepo
from iai_core.repos.project_repo_helpers import ProjectQueryData, ProjectSortBy, ProjectSortDirection
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.project_factory import ProjectFactory
from tests.test_helpers import register_model_template

from geti_types import ID, ProjectIdentifier

WORKSPACE_ID = ID("workspace_id")


class TestProjectRepo:
    def test_project_repo(self, request) -> None:
        """
        <b>Description:</b>
        Check that ProjectRepo can be created, saved and loaded without data being changed

        <b>Input data:</b>
        Classification task, with three labels

        <b>Expected results:</b>
        Label schema in the created project are the same as the label schema in the reloaded ProjectRepo

        <b>Steps</b>
        1. Create Classification Task
        2. Save the task to a ProjectRepo
        3. Reload the Project and test that the label schema did not change
        """
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = ProjectFactory.create_project_single_task(
            name="__Test video tester",
            description="",
            creator_id="",
            labels=[
                {"name": "rectangle", "color": "#00ff00ff"},
                {"name": "ellipse", "color": "#0000ffff"},
                {"name": "triangle", "color": "#ff0000ff"},
            ],
            model_template_id="classification",
        )

        testing_dataset_storage = DatasetStorage(
            name="dummy_testing_dataset_storage",
            project_id=project.id_,
            use_for_training=False,
            _id=DatasetStorageRepo.generate_id(),
        )
        project.dataset_storage_adapters.append(ReferenceAdapter(testing_dataset_storage))
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        project_repo = ProjectRepo()
        project_repo.save(project)
        project_loaded = project_repo.get_by_id(project.id_)
        assert project_loaded == project
        assert testing_dataset_storage in project_loaded.get_dataset_storages()

    def test_project_lock(self, request) -> None:
        """
        <b>Description:</b>
        Check that ProjectRepo can lock a project, and that the lock expires

        <b>Input data:</b>
        Classification task, with three labels

        <b>Expected results:</b>
        Lock active for short period, expiring automatically

        <b>Steps</b>
        1. Create Classification Task
        2. Save the task to a ProjectRepo
        3. Apply lock for 2 seconds, check for lock
        4. Replace lock to be 1 seconds
        5. Wait 1 second
        5. Check lock
        6. Lock, delete lock
        7. Check lock again, to confirm delete works
        """
        # Arrange
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = ProjectFactory.create_project_single_task(
            name="__Test project lock",
            description="",
            creator_id="",
            labels=[
                {"name": "rectangle", "color": "#00ff00ff"},
                {"name": "ellipse", "color": "#0000ffff"},
                {"name": "triangle", "color": "#ff0000ff"},
            ],
            model_template_id="classification",
        )
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
        repo: ProjectRepo = ProjectRepo()
        repo.save(project)

        # Act & Assert
        assert repo.read_lock(project.id_) is False
        repo.mark_locked("train", project.id_, 1)
        repo.mark_locked("test", project.id_, 1)
        repo.mark_locked("optimize", project.id_, 2)

        assert repo.read_lock(project.id_) is True
        # Wait for first lock to expire
        time.sleep(1.1)
        assert repo.read_lock(project.id_) is True  # one lock still active
        # Wait for all locks to be expired
        time.sleep(1)
        assert repo.read_lock(project.id_) is False
        # Lock and unlock immediately
        repo.mark_locked("train", project.id_, 100)
        repo.mark_unlocked("train", project.id_)
        # Confirm unlock works
        assert repo.read_lock(project.id_) is False

    def test_project_hiding(self, request, fxt_empty_project) -> None:
        """
        <b>Description:</b>
        Check that ProjectRepo can hide and unhide a project

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The project has the appropriate value for the `hidden` attribute

        <b>Steps</b>
        1. Create a Classification project (not hidden)
        2. Save the project to repo
        3. Hide the project
        4. Check that the project has the proper value for the `hidden` attribute
        5. Make the project visible again
        6. Check that the project has the proper value for the `hidden` attribute
        """
        # Create visible project
        project = fxt_empty_project
        project.id_ = ProjectRepo.generate_id()
        project.hidden = False
        project_repo = ProjectRepo()
        request.addfinalizer(lambda: project_repo.delete_by_id(project.id_))
        # Save it
        project_repo.save(project)
        # Hide it
        project_repo.hide(project)
        project = project_repo.get_by_id(project.id_)
        assert project.hidden
        # Make it visible
        project_repo.unhide(project)
        project = project_repo.get_by_id(project.id_)
        assert not project.hidden

    def test_dataset_in_project_repo(self, request) -> None:
        """
        <b>Description:</b>
        Check that dataset storage remains unchanged when saving and retrieving a project.

        <b>Input data:</b>
        An empty Workspace and DatasetStorage, two empty projects.

        <b>Expected results:</b>
        Saving and fetching a project results in the same DatasetStorage and Workspace being connected to the project.

        <b>Steps</b>
        1. Initialize project and dataset_storage repo
        2. Initialize a dataset storage and save it to the repo
        3. Create a project with the initialized dataset storage
        4. Save the project and fetch them it the repo
        5. Compare the initial and the fetched DatasetStorage for the project and assert they are equal
        """
        project_id = ProjectRepo.generate_id()
        project_identifier = ProjectIdentifier(workspace_id=WORKSPACE_ID, project_id=project_id)

        dataset_storage_repo = DatasetStorageRepo(project_identifier)
        dataset_storage1 = DatasetStorage(
            name="dataset1",
            project_id=project_id,
            _id=DatasetStorageRepo.generate_id(),
            use_for_training=True,
        )
        dataset_storage_repo.save(dataset_storage1)

        project1 = Project(
            name="project1",
            creator_id="",
            description="project1",
            dataset_storages=[dataset_storage1],
            id=project_id,
        )

        project_repo = ProjectRepo()

        project_repo.save(project1)
        request.addfinalizer(lambda: dataset_storage_repo.delete_by_id(dataset_storage1.id_))

        project1_loaded = project_repo.get_by_id(project1.id_)

        compare(
            project1_loaded.get_training_dataset_storage(),
            project1.get_training_dataset_storage(),
        )
        assert dataset_storage1 == project1.get_training_dataset_storage()

    def test_get_project_by_dataset_storage_id(self, request, fxt_model_template_classification) -> None:
        """
        <b>Description:</b>
        Check that a project can be found by a dataset_storage_id

        <b>Input data:</b>
        Classification task, with one label

        <b>Expected results:</b>
        Each project loaded by the dataset_storage_id is the same as the original project

        <b>Steps</b>
        1. Create Classification Task
        2. Assert that the project has at least 1 dataset_storage_id
        3. Get the project using each ID in dataset_storage_ids and compare to original
        """
        project_original = ProjectFactory.create_project_single_task(
            name="test_get_project_by_dataset_storage_id",
            description="",
            creator_id="",
            labels=[
                {"name": "a", "color": "#00ff00ff"},
            ],
            model_template_id=fxt_model_template_classification,
        )
        ProjectRepo().save(project_original)
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project_original.id_))

        assert len(project_original.dataset_storage_ids) > 0

        for dataset_storage_id in project_original.dataset_storage_ids:
            project_loaded = ProjectRepo().get_by_dataset_storage_id(dataset_storage_id)
            compare(project_loaded, project_original)

    def test_get_names(
        self,
        request,
        fxt_ote_id,
        fxt_model_template_classification,
    ) -> None:
        """
        <b>Description:</b>
        Check that permitted projects names can be retrieved

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Projects names retrieved by get_names are same as for the original projects.

        <b>Steps</b>
        1. Create 4 projects
        2. Fetch the projects names with a list of permitted ones
        3. Check if the retrieved projects names are the expected ones
        """
        repo: ProjectRepo = ProjectRepo()
        for proj in repo.get_all():
            repo.delete_by_id(proj.id_)

        permitted_project_num = 2
        project_names = ["alfa", "Beta", "gamma", "Delta"]
        project_list = []
        permitted_projects = []
        for idx, project_name in enumerate(project_names):
            project = ProjectFactory.create_project_single_task(
                name=project_name,
                creator_id="",
                description="",
                labels=[
                    {"name": "a", "color": "#00ff00ff"},
                ],
                model_template_id=fxt_model_template_classification,
                hidden=False,
            )
            request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
            project_list.append(project)
            if idx < permitted_project_num:
                permitted_projects.append(project.id_)

        loaded_projects_names = repo.get_names(permitted_projects=tuple(permitted_projects))
        projects_names = {project.id_: project.name for project in project_list if project.id_ in permitted_projects}
        compare(loaded_projects_names, projects_names)

    @pytest.mark.parametrize(
        "include_hidden,sort_by,sort_direction",
        [
            (True, ProjectSortBy.CREATION_DATE, ProjectSortDirection.ASC),
            (False, ProjectSortBy.CREATION_DATE, ProjectSortDirection.DSC),
            (False, ProjectSortBy.NAME, ProjectSortDirection.ASC),
            (True, ProjectSortBy.NAME, ProjectSortDirection.DSC),
        ],
        ids=[
            "include hidden, sort by creation date ascending",
            "exclude hidden, sort by creation date descending",
            "exclude hidden, sort by name ascending",
            "include hidden, sort by name descending",
        ],
    )
    def test_get_by_page(
        self,
        request,
        include_hidden,
        sort_by,
        sort_direction,
        fxt_ote_id,
        fxt_model_template_classification,
    ) -> None:
        """
        <b>Description:</b>
        Check that project list can be retrieved with pagination

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Projects retrieved by get_project_by_page are same as the original projects.
        Projects should be sorted case-insensitive if sorted by name.

        <b>Steps</b>
        1. Create 4 projects (first one may be hidden)
        2. Fetch the projects in pages of max 2 projects
        3. Check if the retrieved projects are the expected ones
        """
        repo: ProjectRepo = ProjectRepo()
        for proj in repo.get_all():
            repo.delete_by_id(proj.id_)

        num_projects = 4
        project_names = ["alfa", "Beta", "camma", "Delta"]
        project_list = []
        for i in range(num_projects):
            project = ProjectFactory.create_project_single_task(
                name=f"{project_names[i]}_{i}",
                description="",
                creator_id="",
                labels=[
                    {"name": "a", "color": "#00ff00ff"},
                ],
                model_template_id=fxt_model_template_classification,
                hidden=(i == 0),
            )
            request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
            project_list.append(project)
        project_list.sort(
            key=lambda project: project.name.lower() if sort_by == ProjectSortBy.NAME else project.creation_date,
            reverse=(sort_direction == ProjectSortDirection.DSC),
        )
        query_data: ProjectQueryData = ProjectQueryData(
            skip=0,
            limit=2,
            name="",
            sort_by=sort_by,
            sort_direction=sort_direction,
            with_size=False,
        )
        loaded_projects = repo.get_by_page(query_data=query_data, include_hidden=include_hidden)
        query_data.skip = len(loaded_projects)
        loaded_projects.extend(repo.get_by_page(query_data=query_data, include_hidden=include_hidden))
        non_hidden_projects = [project for project in project_list if not project.hidden]
        if include_hidden:
            compare(loaded_projects, project_list)
        else:
            compare(loaded_projects, non_hidden_projects)

    def test_search_by_name(
        self,
        request,
        fxt_ote_id,
        fxt_model_template_classification,
    ) -> None:
        """
        <b>Description:</b>
        Check that projects can be filtered by name

        <b>Input data:</b>
        5 projects with specific names

        <b>Expected results:</b>
        Projects retrieved by get_project_by_page are filtered by partial
        case-insensitive match on provided string.

        <b>Steps</b>
        1. Create 5 projects with specific names
        2. Fetch the projects filtered by name
        3. Check if the retrieved projects are the expected ones
        """
        # Clean up project repo
        repo: ProjectRepo = ProjectRepo()
        for proj in repo.get_all():
            repo.delete_by_id(proj.id_)

        # Create new projects
        project_names = [
            "Searchone",
            "notrelevant-two",
            "asearchthree",
            "notrelevant-four",
            "sEARch",
            "*.(){}",
        ]
        project_list = []
        for name in project_names:
            project = ProjectFactory.create_project_single_task(
                name=name,
                description="",
                creator_id="",
                labels=[
                    {"name": "a", "color": "#00ff00ff"},
                ],
                model_template_id=fxt_model_template_classification,
            )
            request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
            project_list.append(project)

        # Search projects by name
        query_data: ProjectQueryData = ProjectQueryData(
            skip=0,
            limit=10,
            name="search",
            sort_by=ProjectSortBy.NAME,
            sort_direction=ProjectSortDirection.ASC,
            with_size=False,
        )
        loaded_projects = repo.get_by_page(query_data=query_data)

        regex_query_data: ProjectQueryData = ProjectQueryData(
            skip=0,
            limit=10,
            name="*.(){}",
            sort_by=ProjectSortBy.NAME,
            sort_direction=ProjectSortDirection.ASC,
            with_size=False,
        )
        regex_project = repo.get_by_page(query_data=regex_query_data)

        # Compare result with expected result
        expected_project_names = ["asearchthree", "sEARch", "Searchone"]
        result = [project.name for project in loaded_projects]
        compare(result, expected_project_names)
        assert len(regex_project) == 1
        assert regex_project[0].name == "*.(){}"

    def test_get_permitted_project_by_page(
        self,
        request,
        fxt_ote_id,
        fxt_model_template_classification,
    ) -> None:
        """
        <b>Description:</b>
        Check that project list can be retrieved with filtering by permitted projects and pagination

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Projects retrieved by test_get_permitted_project_by_page are same as the original projects

        <b>Steps</b>
        1. Create 3 projects
        2. Fetch the projects in pages of max 2 projects with first project excluded from permitted list
        3. Check if the retrieved projects are the expected ones
        """
        repo: ProjectRepo = ProjectRepo()
        for proj in repo.get_all():
            repo.delete_by_id(proj.id_)

        num_projects = 3
        project_list = []
        for i in range(num_projects):
            project = ProjectFactory.create_project_single_task(
                name=f"test_project_{i}",
                description="",
                creator_id="",
                labels=[
                    {"name": "a", "color": "#00ff00ff"},
                ],
                model_template_id=fxt_model_template_classification,
                hidden=(i == 0),
            )
            request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))
            project_list.append(project)

        query_data: ProjectQueryData = ProjectQueryData(
            skip=0,
            limit=2,
            name="",
            sort_by=ProjectSortBy.CREATION_DATE,
            sort_direction=ProjectSortDirection.ASC,
            with_size=False,
        )
        loaded_projects = repo.get_by_page(
            query_data=query_data,
            permitted_projects=tuple([p.id_ for p in project_list[1::]]),  # type: ignore
        )
        compare(loaded_projects, project_list[1::])

    def test_count_all_projects(
        self,
        fxt_empty_project,
        fxt_model_template_classification,
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
        repo: ProjectRepo = ProjectRepo()
        for proj in repo.get_all():
            repo.delete_by_id(proj.id_)

        num_projects = 2
        project_ids = []
        for i in range(num_projects):
            project = ProjectFactory.create_project_single_task(
                name=f"test_project_{i}",
                description="",
                creator_id="",
                labels=[
                    {"name": "a", "color": "#00ff00ff"},
                ],
                model_template_id=fxt_model_template_classification,
            )
            project_ids.append(project.id_)
        # Also add a hidden project to check include_hidden param
        fxt_empty_project.hidden = True
        repo.save(fxt_empty_project)
        project_ids.append(fxt_empty_project.id_)
        assert (
            repo.count_all(include_hidden=False, permitted_projects=tuple(project_ids)) == num_projects  # type: ignore
        )
        assert (
            repo.count_all(include_hidden=True, permitted_projects=tuple(project_ids))  # type: ignore
            == num_projects + 1
        )
        assert (
            repo.count_all(include_hidden=False, permitted_projects=tuple(project_ids[1::]))  # type: ignore
            == num_projects - 1
        )
