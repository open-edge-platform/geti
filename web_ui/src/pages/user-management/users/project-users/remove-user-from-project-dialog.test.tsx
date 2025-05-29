// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { createInMemoryUsersService } from '@geti/core/src/users/services/in-memory-users-service';
import { RESOURCE_TYPE, USER_ROLE } from '@geti/core/src/users/users.interface';
import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { useNavigate } from 'react-router-dom';

import { getMockedUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { RemoveUserFromProjectDialog } from './remove-user-from-project-dialog.component';

const mockProjectIdentifier = {
    organizationId: 'organizationId',
    workspaceId: 'workspaceId',
    projectId: 'projectId',
};

jest.mock('../../../../hooks/use-project-identifier/use-project-identifier', () => ({
    ...jest.requireActual('../../../../hooks/use-project-identifier/use-project-identifier'),
    useProjectIdentifier: () => mockProjectIdentifier,
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
}));

describe('RemoveUserFromProjectDialog', () => {
    describe('FEATURE_FLAG_MANAGE_USERS_ROLES: off', () => {
        it('redirects the user after removing itself from a project', async () => {
            const navigate = jest.fn();

            jest.mocked(useNavigate).mockImplementation(() => navigate);

            const activeUser = getMockedUser();
            const dismiss = jest.fn();

            render(<RemoveUserFromProjectDialog activeUser={activeUser} dismiss={dismiss} user={activeUser} />, {
                featureFlags: {
                    FEATURE_FLAG_MANAGE_USERS_ROLES: false,
                },
            });

            await userEvent.click(screen.getByRole('button', { name: /delete/i }));

            await waitFor(() => {
                expect(navigate).toHaveBeenCalledWith(
                    paths.home({
                        organizationId: mockProjectIdentifier.organizationId,
                        workspaceId: mockProjectIdentifier.workspaceId,
                    }),
                    { replace: true }
                );
            });
        });
    });

    describe('FEATURE_FLAG_MANAGE_USERS_ROLES: on', () => {
        it('redirects the user after removing itself from a project', async () => {
            const navigate = jest.fn();

            jest.mocked(useNavigate).mockImplementation(() => navigate);

            const activeUser = getMockedUser({
                roles: [
                    {
                        role: USER_ROLE.PROJECT_CONTRIBUTOR,
                        resourceId: mockProjectIdentifier.projectId,
                        resourceType: RESOURCE_TYPE.PROJECT,
                    },
                ],
            });
            const dismiss = jest.fn();
            const usersService = createInMemoryUsersService();
            usersService.deleteMemberRole = jest.fn();

            render(<RemoveUserFromProjectDialog activeUser={activeUser} dismiss={dismiss} user={activeUser} />, {
                featureFlags: {
                    FEATURE_FLAG_MANAGE_USERS_ROLES: true,
                },
                services: {
                    usersService,
                },
            });

            await userEvent.click(screen.getByRole('button', { name: /delete/i }));

            await waitFor(() => {
                expect(navigate).toHaveBeenCalledWith(
                    paths.home({
                        organizationId: mockProjectIdentifier.organizationId,
                        workspaceId: mockProjectIdentifier.workspaceId,
                    }),
                    { replace: true }
                );
            });

            expect(usersService.deleteMemberRole).toHaveBeenCalledWith(
                mockProjectIdentifier.organizationId,
                activeUser.id,
                {
                    role: activeUser.roles[0].role,
                    resourceId: activeUser.roles[0].resourceId,
                }
            );
        });
    });
});
