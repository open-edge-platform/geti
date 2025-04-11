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
from unittest.mock import patch

from repos.ui_settings_repo import UISettingsRepo
from resource_management.ui_settings_manager import UISettingsManager


class TestUISettingsManager:
    def test_delete_ui_settings_by_project(self, fxt_mongo_id) -> None:
        project_id = fxt_mongo_id(1)
        with patch.object(UISettingsRepo, "delete_all_by_project_id") as mock_delete_settings:
            UISettingsManager.delete_ui_settings_by_project(project_id=project_id)

        mock_delete_settings.assert_called_once_with(project_id=project_id)
