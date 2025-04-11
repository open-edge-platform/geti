// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
