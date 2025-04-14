# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from repos.ui_settings_repo import UISettingsRepo

from geti_types import ID


class UISettingsManager:
    @staticmethod
    def delete_ui_settings_by_project(project_id: ID) -> None:
        """
        Delete UI settings relative to a given project.

        :param project_id: ID of the project
        """
        UISettingsRepo().delete_all_by_project_id(project_id=project_id)
