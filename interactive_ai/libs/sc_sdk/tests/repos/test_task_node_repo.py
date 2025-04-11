#
# INTEL CONFIDENTIAL
# Copyright (c) 2021 Intel Corporation
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material contains trade secrets and proprietary
# and confidential information of Intel or its suppliers and licensors. The
# Material is protected by worldwide copyright and trade secret laws and treaty
# provisions. No part of the Material may be used, copied, reproduced, modified,
# published, uploaded, posted, transmitted, distributed, or disclosed in any way
# without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#


import pytest

from sc_sdk.entities.task_node import NullTaskNode
from sc_sdk.repos import TaskNodeRepo
from sc_sdk.repos.mappers.mongodb_mappers.task_node_mapper import TaskNodeToMongo

from geti_types import ProjectIdentifier


@pytest.mark.ScSdkComponent
class TestTaskNodeRepo:
    def test_task_node_repo(self, fxt_ote_id) -> None:
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        repo = TaskNodeRepo(project_identifier)

        assert repo.forward_map == TaskNodeToMongo.forward
        assert repo.backward_map == TaskNodeToMongo.backward
        assert repo.null_object == NullTaskNode()

    def test_get_trainable_task_ids(self, request, fxt_ote_id, fxt_crop_task, fxt_segmentation_task) -> None:
        """
        <b>Description:</b>
        Check that generator of trainable task ids can be retrieved

        <b>Input data:</b>
        Three tasks of which two are trainable and one of them belongs to another project

        <b>Expected results:</b>
        Test passes if one trainable task id is retrieved.

        <b>Steps</b>
        1. Create test data
        2. Save test data to the repo
        3. Get trainable task ids
        """
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        another_project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(3), project_id=fxt_ote_id(4))

        repo = TaskNodeRepo(project_identifier)
        another_repo = TaskNodeRepo(another_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        request.addfinalizer(lambda: another_repo.delete_all())

        fxt_segmentation_task.id_ = fxt_ote_id(5)
        repo.save(fxt_segmentation_task)
        fxt_crop_task.id_ = fxt_ote_id(6)
        repo.save(fxt_crop_task)
        fxt_segmentation_task.id_ = fxt_ote_id(7)
        another_repo.save(fxt_segmentation_task)

        retrieved_data = set(repo.get_trainable_task_ids())

        assert len(retrieved_data) == 1
        assert retrieved_data.pop() == fxt_ote_id(5)

    def test_get_trainable_task_nodes(self, request, fxt_ote_id, fxt_crop_task, fxt_segmentation_task) -> None:
        """
        <b>Description:</b>
        Check that generator of trainable tasks can be retrieved

        <b>Input data:</b>
        Three tasks of which two are trainable and one of them belongs to another project

        <b>Expected results:</b>
        Test passes if one trainable task node is retrieved.

        <b>Steps</b>
        1. Create test data
        2. Save test data to the repo
        3. Get trainable task nodes
        """
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        another_project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(3), project_id=fxt_ote_id(4))

        repo = TaskNodeRepo(project_identifier)
        another_repo = TaskNodeRepo(another_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        request.addfinalizer(lambda: another_repo.delete_all())

        fxt_segmentation_task.id_ = fxt_ote_id(5)
        repo.save(fxt_segmentation_task)
        fxt_crop_task.id_ = fxt_ote_id(6)
        repo.save(fxt_crop_task)
        fxt_segmentation_task.id_ = fxt_ote_id(7)
        another_repo.save(fxt_segmentation_task)

        retrieved_data = set(repo.get_trainable_task_nodes())

        assert len(retrieved_data) == 1
        retrieved_task = retrieved_data.pop()
        assert retrieved_task._task_properties.is_trainable
        assert retrieved_task.id_ == fxt_ote_id(5)
