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

from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ChangesetMetadata:
    """Metadata relative to a changeset"""

    description: str  # Understandable description of the changeset and its migration script
    supports_downgrade: bool  # Whether the migration script supports the downgrade path
    skip_on_project_import: bool  # Whether the migration script should be skipped on project import
    affects_binary_data: bool  # Whether the script modifies the layout/content of the object storage
    new_collections: list[str]  # List of collections created by the script
    updated_collections: list[str]  # List of collections modified by the script
    deprecated_collections: list[str]  # List of collections removed by the script
