// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedWorkspaceIdentifier } from '../../test-utils/mocked-items-factory/mocked-identifiers';
import {
    getMockedAdminUser,
    getMockedOrganizationAdminUser,
    getMockedUser,
} from '../../test-utils/mocked-items-factory/mocked-users';
import { isOrganizationAdmin, isWorkspaceAdmin, isWorkspaceContributor } from './user-role-utils';
import { RESOURCE_TYPE, USER_ROLE } from './users.interface';

describe('Role utils', () => {
    const { workspaceId, organizationId } = getMockedWorkspaceIdentifier();
    const mockedOrgAdmin = getMockedOrganizationAdminUser({}, workspaceId, organizationId);
    const mockedWorkspaceAdmin = getMockedAdminUser({}, workspaceId);
    const mockedUser = getMockedUser();

    it('Check isOrganizationAdmin', () => {
        expect(isOrganizationAdmin(mockedOrgAdmin, organizationId)).toBeTruthy();
        expect(isOrganizationAdmin(mockedWorkspaceAdmin, organizationId)).toBeFalsy();
        expect(isOrganizationAdmin(mockedUser, organizationId)).toBeFalsy();
    });

    it('Check isWorkspaceAdmin', () => {
        expect(isWorkspaceAdmin(mockedOrgAdmin, workspaceId)).toBeTruthy();
        expect(isWorkspaceAdmin(mockedWorkspaceAdmin, workspaceId)).toBeTruthy();
        expect(isWorkspaceAdmin(mockedUser, workspaceId)).toBeFalsy();
    });

    it('isWorkspaceContributor', () => {
        const mockedWorkspaceContributor = getMockedUser({
            roles: [
                {
                    resourceType: RESOURCE_TYPE.WORKSPACE,
                    role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                    resourceId: workspaceId,
                },
            ],
        });

        const mockedWorkspaceContributorWithDifferentWorkspaceId = getMockedUser({
            roles: [
                {
                    resourceType: RESOURCE_TYPE.WORKSPACE,
                    role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                    resourceId: 'different-workspace-id',
                },
            ],
        });

        expect(isWorkspaceContributor(mockedWorkspaceContributor, workspaceId)).toBe(true);
        expect(isWorkspaceContributor(mockedWorkspaceAdmin, workspaceId)).toBe(false);
        expect(isWorkspaceContributor(mockedWorkspaceContributorWithDifferentWorkspaceId, workspaceId)).toBe(false);
    });
});
