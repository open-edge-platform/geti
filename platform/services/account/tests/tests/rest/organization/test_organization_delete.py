# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.organization import Organization, OrganizationWithAdmins


def test_delete_organization():
    org = Organization.randomize()
    org.create()
    org.delete()

    assert OrganizationWithAdmins.get(org.id) is None
