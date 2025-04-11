# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.organization import Organization
from models.user import User
from models.workspace import Workspace


class ComplexRolesModelPlayground:
    def __enter__(self):
        self.org_to_be_deleted = Organization.randomize()
        self.org_to_be_deleted.create()

        self.workspace_0_to_be_deleted = Workspace.randomize(organization_id=self.org_to_be_deleted.id)
        self.workspace_0_to_be_deleted.create()
        self.workspace_1_to_be_deleted = Workspace.randomize(organization_id=self.org_to_be_deleted.id)
        self.workspace_1_to_be_deleted.create()

        self.org_to_stay = Organization.randomize()
        self.org_to_stay.create()

        self.workspace_to_stay = Workspace.randomize(organization_id=self.org_to_stay.id)
        self.workspace_to_stay.create()

        self.user0 = User.randomize(organization_id=self.org_to_be_deleted.id)
        self.user0.create()

        self.user1 = User.randomize(organization_id=self.org_to_be_deleted.id)
        self.user1.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.user1.delete()
            self.user0.delete()
            self.workspace_to_stay.delete()
            self.workspace_1_to_be_deleted.delete()
            self.workspace_0_to_be_deleted.delete()
            self.org_to_stay.delete()
            self.org_to_be_deleted.delete()
        except AssertionError:
            # ignore deletion's 404s because some models might be deleted during tests
            pass
