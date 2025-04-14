# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

from repos.ui_settings_repo import UISettingsRepo
from resource_management.ui_settings_manager import UISettingsManager


class TestUISettingsManager:
    def test_delete_ui_settings_by_project(self, fxt_mongo_id) -> None:
        project_id = fxt_mongo_id(1)
        with patch.object(UISettingsRepo, "delete_all_by_project_id") as mock_delete_settings:
            UISettingsManager.delete_ui_settings_by_project(project_id=project_id)

        mock_delete_settings.assert_called_once_with(project_id=project_id)
