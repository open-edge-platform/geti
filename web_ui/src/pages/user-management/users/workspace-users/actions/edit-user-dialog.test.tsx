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

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { createInMemoryUsersService } from '../../../../../core/users/services/in-memory-users-service';
import { RESOURCE_TYPE, USER_ROLE } from '../../../../../core/users/users.interface';
import { applicationRender as render } from '../../../../../test-utils/application-provider-render';
import { getMockedWorkspaceIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedAdminUser, getMockedUser } from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { getMockedWorkspace } from '../../../../../test-utils/mocked-items-factory/mocked-workspace';
import { EditUserDialog } from './edit-user-dialog.component';

const mockedWorkspaceIdentifier = getMockedWorkspaceIdentifier({ workspaceId: 'testing-workspace' });
const mockedAdminUser = getMockedAdminUser(
    { firstName: 'John', lastName: 'Snow', id: 'user-id' },
    mockedWorkspaceIdentifier.workspaceId
);
const mockedWorkspace = getMockedWorkspace({ id: mockedWorkspaceIdentifier.workspaceId, name: 'Workspace 1' });

jest.mock('../../../../../providers/workspaces-provider/workspaces-provider.component', () => ({
    ...jest.requireActual('../../../../../providers/workspaces-provider/workspaces-provider.component'),
    useWorkspaces: jest.fn(() => ({
        workspaces: [mockedWorkspace],
        workspaceId: mockedWorkspaceIdentifier.workspaceId,
    })),
}));

describe('EditUserDialog', () => {
    describe('WORKSPACE_ACTION FF enabled', () => {
        it('save button is disabled when member data has not been changed', async () => {
            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[mockedAdminUser]}
                />,
                { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false } }
            );

            expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
        });

        it('Check edit dialog on SaaS environment', async () => {
            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[mockedAdminUser, getMockedAdminUser({ id: 'user-id-2' })]}
                />,
                { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: true } }
            );

            expect(screen.getByText('Edit user')).toBeInTheDocument();
            expect(screen.getByTestId('user-email')).toHaveTextContent(mockedAdminUser.email);
            expect(screen.getByTestId('last-successful-login-John-Snow')).toHaveTextContent(
                'Last login:14 Aug 202311:13 AM'
            );

            expect(screen.getByLabelText('First name')).toBeDisabled();
            expect(screen.getByLabelText('Last name')).toBeDisabled();

            expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();

            expect(screen.getByTestId('edit-workspace-role-Workspace 1')).toBeInTheDocument();
            expect(screen.getByTestId('roles-add-user')).toHaveTextContent('Admin');
            expect(screen.getByRole('button', { name: 'Add workspace role' })).toBeDisabled();
        });

        it('Check edit dialog on on-prem environment', async () => {
            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment={false}
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[
                        mockedAdminUser,
                        getMockedAdminUser({ id: 'user-id-2' }, mockedWorkspaceIdentifier.workspaceId),
                    ]}
                />,
                { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: true } }
            );

            expect(screen.getByText('Edit user')).toBeInTheDocument();
            expect(screen.getByTestId('user-email')).toHaveTextContent(mockedAdminUser.email);
            expect(screen.getByTestId('last-successful-login-John-Snow')).toHaveTextContent(
                'Last login:14 Aug 202311:13 AM'
            );

            expect(screen.getByLabelText('First name')).toBeEnabled();
            expect(screen.getByLabelText('Last name')).toBeEnabled();

            expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();

            expect(screen.getByTestId('edit-workspace-role-Workspace 1')).toBeInTheDocument();
            expect(screen.getByTestId('roles-add-user')).toHaveTextContent('Admin');
            expect(screen.getByRole('button', { name: 'Add workspace role' })).toBeDisabled();
        });
    });

    describe('WORKSPACE_ACTION FF disabled', () => {
        it('save button is disabled when member data has not been changed', async () => {
            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[mockedAdminUser]}
                />,
                { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false } }
            );

            expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
        });

        it('Check edit dialog on SaaS environment', async () => {
            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[
                        mockedAdminUser,
                        getMockedAdminUser({ id: 'user-id-2' }, mockedWorkspaceIdentifier.workspaceId),
                    ]}
                />,
                { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false } }
            );

            expect(screen.getByText('Edit user')).toBeInTheDocument();
            expect(screen.getByTestId('user-email')).toHaveTextContent(mockedAdminUser.email);
            expect(screen.getByTestId('last-successful-login-John-Snow')).toHaveTextContent(
                'Last login:14 Aug 202311:13 AM'
            );

            expect(screen.getByLabelText('First name')).toBeDisabled();
            expect(screen.getByLabelText('Last name')).toBeDisabled();

            expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /role/i }));

            await userEvent.selectOptions(
                screen.getByRole('listbox', { name: 'Role' }),
                screen.getByRole('option', { name: /Contributor/ })
            );
        });

        describe('roles edition', () => {
            it("edits member's role", async () => {
                const usersService = createInMemoryUsersService();
                usersService.updateMemberRole = jest.fn();

                await render(
                    <EditUserDialog
                        organizationId={mockedWorkspaceIdentifier.organizationId}
                        workspaceId={mockedWorkspaceIdentifier.workspaceId}
                        user={mockedAdminUser}
                        isSaasEnvironment
                        closeDialog={jest.fn()}
                        activeUser={mockedAdminUser}
                        users={[
                            mockedAdminUser,
                            getMockedAdminUser({ id: 'user-id-2' }, mockedWorkspaceIdentifier.workspaceId),
                        ]}
                    />,
                    {
                        featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false, FEATURE_FLAG_MANAGE_USERS_ROLES: true },
                        services: {
                            usersService,
                        },
                    }
                );

                await userEvent.click(screen.getByRole('button', { name: /role/i }));
                await userEvent.selectOptions(
                    screen.getByRole('listbox', { name: 'Role' }),
                    screen.getByRole('option', { name: /Contributor/ })
                );

                await userEvent.click(screen.getByRole('button', { name: 'Save' }));

                await waitFor(() => {
                    expect(usersService.updateMemberRole).toHaveBeenCalledWith(
                        mockedWorkspaceIdentifier.organizationId,
                        mockedAdminUser.id,
                        {
                            resourceId: mockedWorkspaceIdentifier.organizationId,
                            role: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
                        }
                    );
                });
            });
        });

        it('active member cannot edit member role when their role is a workspace contributor', async () => {
            const memberContributor = getMockedUser({
                roles: [
                    {
                        role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        resourceId: mockedWorkspaceIdentifier.workspaceId,
                    },
                ],
            });
            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={memberContributor}
                    users={[memberContributor, mockedAdminUser]}
                />,
                {
                    featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false, FEATURE_FLAG_MANAGE_USERS_ROLES: true },
                }
            );

            expect(screen.queryByRole('button', { name: /role/i })).not.toBeInTheDocument();
        });

        it('active member cannot edit member their role when active member is the only workspace admin', async () => {
            const memberContributor = getMockedUser({
                roles: [
                    {
                        role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        resourceId: mockedWorkspaceIdentifier.workspaceId,
                    },
                ],
            });

            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[memberContributor, mockedAdminUser]}
                />,
                {
                    featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false, FEATURE_FLAG_MANAGE_USERS_ROLES: true },
                }
            );

            expect(screen.queryByRole('button', { name: /role/i })).not.toBeInTheDocument();
        });

        it('active member can edit member other member role when active member is a workspace admin', async () => {
            const memberContributor = getMockedUser({
                roles: [
                    {
                        role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        resourceId: mockedWorkspaceIdentifier.workspaceId,
                    },
                ],
            });

            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={memberContributor}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[memberContributor, mockedAdminUser]}
                />,
                {
                    featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false, FEATURE_FLAG_MANAGE_USERS_ROLES: true },
                }
            );

            await userEvent.click(screen.getByRole('button', { name: /role/i }));

            expect(screen.getByRole('option', { name: /Contributor/ })).toBeInTheDocument();
            expect(screen.getByRole('option', { name: /Admin/ })).toBeInTheDocument();
        });

        it('active member can edit member their role when there are more admins than one', async () => {
            await render(
                <EditUserDialog
                    organizationId={mockedWorkspaceIdentifier.organizationId}
                    workspaceId={mockedWorkspaceIdentifier.workspaceId}
                    user={mockedAdminUser}
                    isSaasEnvironment
                    closeDialog={jest.fn()}
                    activeUser={mockedAdminUser}
                    users={[
                        mockedAdminUser,
                        getMockedAdminUser({ id: 'user-id-2' }, mockedWorkspaceIdentifier.workspaceId),
                    ]}
                />,
                {
                    featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: false, FEATURE_FLAG_MANAGE_USERS_ROLES: true },
                }
            );

            await userEvent.click(screen.getByRole('button', { name: /role/i }));

            expect(screen.getByRole('option', { name: /Contributor/ })).toBeInTheDocument();
            expect(screen.getByRole('option', { name: /Admin/ })).toBeInTheDocument();
        });
    });
});
