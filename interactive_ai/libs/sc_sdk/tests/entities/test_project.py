# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""This module tests the Project class"""

import pytest

from sc_sdk.adapters.adapter import IAdapter, ProxyAdapter
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_graph import NullTaskGraph


@pytest.mark.ScSdkComponent
class TestProject:
    def test_project_construction(self, fxt_ote_id) -> None:
        """
        <b>Description:</b>
        Check that project is initialised correctly

        Checking for:
        - Name
        - Description
        - Creator ID
        - Dataset storages
        - Training dataset storage

        <b>Input data:</b>
        Workspace, dataset storage and project

        <b>Expected results:</b>
        All assertions pass

        <b>Steps</b>
        1. Create Workspace
        2. Create Dataset storage
        3. Create Project
        4. Assert name, description, creator id, and check if dataset storages match
        """
        name = "test project"
        description = "project for testing"
        creator_id = "test"
        project_id = fxt_ote_id(3)

        dataset_storages = [
            DatasetStorage(
                name="test",
                project_id=project_id,
                _id=fxt_ote_id(2),
                use_for_training=True,
            )
        ]

        project = Project(
            id=project_id,
            name=name,
            creator_id=creator_id,
            description=description,
            dataset_storages=dataset_storages,
            task_graph=NullTaskGraph(),
        )

        assert project.name == name
        assert project.description == description
        assert project.creator_id == creator_id
        assert project.get_dataset_storages() == tuple(dataset_storages)
        assert project.get_training_dataset_storage() == dataset_storages[0]

    def test_project_construction_with_adapters(self, fxt_ote_id) -> None:
        """
        <b>Description:</b>
        Check that project is initialised correctly with the method `with_adapters`

        Checking for:
        - Name
        - Description
        - Creator ID
        - Dataset storages
        - Training dataset storage
        - Runtime error when no dataset storage adapters are provided


        <b>Input data:</b>
        Workspace, dataset storage and project

        <b>Expected results:</b>
        All assertions pass and errors raised

        <b>Steps</b>
        1. Create Workspace
        2. Create Dataset storage
        3. Create Project
        4. Assert name, description, creator id, and check if dataset storages match
        5. Check if runtime error ir raised when project is created with empty
           dataset storage adapters
        """
        name = "test project"
        description = "project for testing"
        creator_id = "test"
        project_id = fxt_ote_id(7)

        dataset_storages = [
            DatasetStorage(
                name="test",
                project_id=project_id,
                _id=fxt_ote_id(5),
                use_for_training=True,
            )
        ]

        training_dataset_storage_adapter = ProxyAdapter(
            id=fxt_ote_id(6),
            proxy=lambda: dataset_storages[0],
        )

        dataset_storage_adapters: list[IAdapter[DatasetStorage]] = [
            ProxyAdapter(id=fxt_ote_id(7), proxy=lambda: dataset_storages[0])
        ]

        project = Project.with_adapters(
            training_dataset_storage_adapter=training_dataset_storage_adapter,
            dataset_storage_adapters=dataset_storage_adapters,
            name=name,
            id=project_id,
            creator_id=creator_id,
            description=description,
        )

        assert project.name == name
        assert project.description == description
        assert project.creator_id == creator_id
        assert project.get_dataset_storages() == tuple(dataset_storages)
        assert project.get_training_dataset_storage() == dataset_storages[0]
        with pytest.raises(RuntimeError):
            Project.with_adapters(
                training_dataset_storage_adapter=training_dataset_storage_adapter,
                dataset_storage_adapters=[],
                name=name,
                id=fxt_ote_id(8),
                creator_id=creator_id,
                description=description,
            )
