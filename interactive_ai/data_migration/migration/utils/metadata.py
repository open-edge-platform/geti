# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
