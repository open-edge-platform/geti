# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

import abc


class IMigrationScript(metaclass=abc.ABCMeta):
    """
    Base class for all migration scripts.

    The interface provides methods to upgrade/downgrade project and non-project data.
    'Project data' refers to entities and relationships that are bound to a project, for example media and models.
    'Non-project data' is not tied to one specific project, or is at a higher hierarchy level (e.g. workspaces, jobs).
    Project data shall be migrated with 'upgrade_project', which also runs on project import so that previously
    exported projects can be eventually upgraded to the latest data version without breaking.
    Conversely, 'upgrade_non_project_data' only executes on platform update but not on project import.

    Every migration scripts shall explicitly define all methods, however the implementation of some methods may be
    as simple as a "pass" statement if such method does not apply (no data to transform).
    """

    @classmethod
    @abc.abstractmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Upgrade data relative to a specific project.

        Important: the operation must be idempotent and tolerate failures/exception as much as possible.

        :param organization_id: ID of the organization that owns the workspace
        :param workspace_id: ID of the workspace that contains the project
        :param project_id: ID of the project to upgrade
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Downgrade data relative to a specific project. This is the inverse of 'upgrade_project'.

        Important: the operation must be idempotent and tolerate failures/exception as much as possible.

        :param organization_id: ID of the organization that owns the workspace
        :param workspace_id: ID of the workspace that contains the project
        :param project_id: ID of the project to downgrade
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def upgrade_non_project_data(cls) -> None:
        """
        Upgrade data that does not fall within the scope of any specific project.

        Important: the operation must be idempotent and tolerate failures/exception as much as possible.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def downgrade_non_project_data(cls) -> None:
        """
        Downgrade data that does not fall within the scope of any specific project.
        This is the inverse of 'upgrade_non_project_data'.

        Important: the operation must be idempotent and tolerate failures/exception as much as possible.
        """
        raise NotImplementedError
