// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { RESOURCE_TYPE, USER_ROLE } from '../../../../core/users/users.interface';
import { getMockedWorkspaceIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedAdminUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { getMockedWorkspace } from '../../../../test-utils/mocked-items-factory/mocked-workspace';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { InviteUser } from './invite-user.component';

const mockedAdmin = getMockedAdminUser();
const mockedInviteUserMutation = jest.fn();
const mockedWorkspaceIdentifier = getMockedWorkspaceIdentifier();
const mockedInvalidateQuery = jest.fn();
const MockedWorkspace = getMockedWorkspace({ id: mockedWorkspaceIdentifier.workspaceId });

jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useQueryClient: () => ({
        invalidateQueries: mockedInvalidateQuery,
    }),
}));

jest.mock('../../../../providers/workspaces-provider/workspaces-provider.component', () => ({
    ...jest.requireActual('../../../../providers/workspaces-provider/workspaces-provider.component'),
    useWorkspaces: jest.fn(() => ({
        workspaceId: mockedWorkspaceIdentifier.workspaceId,
        workspaces: [MockedWorkspace],
    })),
}));

jest.mock('../../../../core/users/hook/use-users.hook', () => ({
    useUsers: jest.fn(() => ({
        useGetUsersQuery: jest.fn(() => ({ data: [] })),
        useInviteUserMutation: jest.fn(() => ({ isPending: false, mutate: mockedInviteUserMutation })),
    })),
}));

describe('Invite user to the workspace', () => {
    it('Check if user invitation is sending proper roles', async () => {
        render(
            <InviteUser
                isAdmin={mockedAdmin.isAdmin}
                id={mockedAdmin.id}
                organizationId={mockedWorkspaceIdentifier.organizationId}
                workspaceId={mockedWorkspaceIdentifier.workspaceId}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Send invite' }));
        const emailInput = screen.getByLabelText('Email address');
        fireEvent.change(emailInput, { target: { value: 'test@intel.com' } });

        fireEvent.submit(screen.getByRole('button', { name: 'send invitation' }));

        expect(mockedInviteUserMutation).toHaveBeenCalledWith(
            expect.objectContaining({
                roles: [
                    {
                        resourceId: mockedWorkspaceIdentifier.workspaceId,
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                    },
                    {
                        resourceId: mockedWorkspaceIdentifier.organizationId,
                        resourceType: RESOURCE_TYPE.ORGANIZATION,
                        role: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
                    },
                ],
            }),
            expect.objectContaining({})
        );
    });

    it('Check if admin can invite user to the workspace - admin and contributor role', async () => {
        render(
            <InviteUser
                isAdmin={mockedAdmin.isAdmin}
                id={mockedAdmin.id}
                organizationId={mockedWorkspaceIdentifier.organizationId}
                workspaceId={mockedWorkspaceIdentifier.workspaceId}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Send invite' }));
        fireEvent.click(screen.getByRole('button', { name: 'Contributor Role' }));

        expect(screen.getByRole('option', { name: USER_ROLE.WORKSPACE_CONTRIBUTOR })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: USER_ROLE.WORKSPACE_ADMIN })).toBeInTheDocument();
    });

    it('Check if contributor can invite user to the workspace - contributor role', async () => {
        render(
            <InviteUser
                isAdmin={false}
                id={mockedAdmin.id}
                organizationId={mockedWorkspaceIdentifier.organizationId}
                workspaceId={mockedWorkspaceIdentifier.workspaceId}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Send invite' }));
        fireEvent.click(screen.getByRole('button', { name: 'Contributor Role' }));

        expect(screen.getByRole('option', { name: 'Contributor' })).toBeInTheDocument();
    });
});
