// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { createInMemoryUsersService } from '../../../../core/users/services/in-memory-users-service';
import { RESOURCE_TYPE, USER_ROLE } from '../../../../core/users/users.interface';
import {
    getMockedOrganizationAdminUser,
    getMockedOrganizationContributorUser,
    getMockedUser,
} from '../../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { EditUserRoleDialog } from './edit-user-role-dialog.component';

const mockProjectIdentifier = {
    organizationId: 'organization-id',
    workspaceId: 'workspaceId',
    projectId: 'projectId',
};

jest.mock('../../../../hooks/use-project-identifier/use-project-identifier', () => ({
    ...jest.requireActual('../../../../hooks/use-project-identifier/use-project-identifier'),
    useProjectIdentifier: () => mockProjectIdentifier,
}));

describe('EditUserRoleDialog', () => {
    it('displays current user role', async () => {
        const activeUser = getMockedOrganizationAdminUser();
        const user = getMockedUser({
            roles: [
                {
                    role: USER_ROLE.PROJECT_MANAGER,
                    resourceId: mockProjectIdentifier.projectId,
                    resourceType: RESOURCE_TYPE.PROJECT,
                },
            ],
        });

        render(<EditUserRoleDialog user={user} activeUser={activeUser} dismiss={jest.fn} />);

        expect(screen.getByRole('button', { name: /Project manager/ })).toBeVisible();
    });

    describe('when user is organization admin or workspace admin', () => {
        it.each([
            getMockedOrganizationAdminUser(),
            getMockedUser({
                roles: [
                    {
                        role: USER_ROLE.WORKSPACE_ADMIN,
                        resourceId: mockProjectIdentifier.workspaceId,
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                    },
                ],
            }),
        ])("edits user's role", async (activeUser) => {
            const user = getMockedUser({
                roles: [
                    {
                        role: USER_ROLE.PROJECT_MANAGER,
                        resourceId: mockProjectIdentifier.projectId,
                        resourceType: RESOURCE_TYPE.PROJECT,
                    },
                ],
            });

            const usersService = createInMemoryUsersService();
            usersService.updateMemberRole = jest.fn();

            render(<EditUserRoleDialog user={user} activeUser={activeUser} dismiss={jest.fn} />, {
                featureFlags: { FEATURE_FLAG_MANAGE_USERS_ROLES: true },
                services: { usersService },
            });

            await userEvent.click(screen.getByRole('button', { name: /Project manager/ }));

            expect(screen.getAllByRole('option')).toHaveLength(2);
            expect(screen.getByRole('option', { name: /Project manager/ })).toBeVisible();
            expect(screen.getByRole('option', { name: /Project contributor/ })).toBeVisible();

            await userEvent.selectOptions(
                screen.getByRole('listbox', { name: 'Role' }),
                screen.getByRole('option', { name: /Project contributor/ })
            );

            await userEvent.click(screen.getByRole('button', { name: 'Save' }));

            expect(usersService.updateMemberRole).toHaveBeenCalledWith(mockProjectIdentifier.organizationId, user.id, {
                role: 'Project contributor',
                resourceId: mockProjectIdentifier.projectId,
            });
        });
    });

    describe('when user is organization contributor or workspace contributor', () => {
        const organizationContributor = getMockedOrganizationContributorUser();
        const workspaceContributor = getMockedUser({
            roles: [
                {
                    role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                    resourceId: mockProjectIdentifier.workspaceId,
                    resourceType: RESOURCE_TYPE.WORKSPACE,
                },
            ],
        });

        it.each([organizationContributor, workspaceContributor])("edits user's role", async (activeUser) => {
            const user = getMockedUser({
                roles: [
                    {
                        role: USER_ROLE.PROJECT_CONTRIBUTOR,
                        resourceId: mockProjectIdentifier.projectId,
                        resourceType: RESOURCE_TYPE.PROJECT,
                    },
                ],
            });

            const usersService = createInMemoryUsersService();
            usersService.updateMemberRole = jest.fn();

            render(<EditUserRoleDialog user={user} activeUser={activeUser} dismiss={jest.fn} />, {
                featureFlags: { FEATURE_FLAG_MANAGE_USERS_ROLES: true },
                services: { usersService },
            });

            await userEvent.click(screen.getByRole('button', { name: /Project contributor/ }));

            expect(screen.getAllByRole('option')).toHaveLength(1);

            await userEvent.selectOptions(
                screen.getByRole('listbox', { name: 'Role' }),
                screen.getByRole('option', { name: /Project contributor/ })
            );

            await userEvent.click(screen.getByRole('button', { name: 'Save' }));

            expect(usersService.updateMemberRole).toHaveBeenCalledWith(mockProjectIdentifier.organizationId, user.id, {
                role: 'Project contributor',
                resourceId: mockProjectIdentifier.projectId,
            });
        });
    });
});
