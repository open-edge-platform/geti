// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { AccountStatus } from '../../../../../core/organizations/organizations.interface';
import { Resource, RESOURCE_TYPE } from '../../../../../core/users/users.interface';
import { applicationRender as render } from '../../../../../test-utils/application-provider-render';
import { getMockedWorkspaceIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import {
    getMockedAdminUser,
    getMockedContributorUser,
    getMockedOrganizationAdminUser,
    getMockedUser,
} from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { WorkspaceUserActions } from './workspace-user-actions.component';

const mockedWorkspaceIdentifier = getMockedWorkspaceIdentifier({ workspaceId: 'workspace_1' });
const { workspaceId, organizationId } = mockedWorkspaceIdentifier;

const mockedOrgAdminUser = getMockedOrganizationAdminUser({ id: 'user-admin-id' }, workspaceId, organizationId);
const mockedOrgAdminUser2 = getMockedOrganizationAdminUser({ id: 'user-admin-2-id' }, workspaceId, organizationId);
const mockedContributorUser = getMockedContributorUser({ id: 'contributor-user-1' }, workspaceId);
const mockedContributorUser2 = getMockedContributorUser({ id: 'contributor-user-2' }, workspaceId);
const mockedWorkspaceAdminUser = getMockedAdminUser({
    firstName: 'Admin',
    lastName: 'Second',
    id: 'user-workspace-admin-id',
});
const mockedInvitedUser = getMockedUser({
    firstName: 'Jan',
    lastName: 'Kowalski',
    id: 'jan-kowalski-id',
    status: AccountStatus.INVITED,
});

const mockedUseProductInfo = jest.fn();
const mockedUseActiveUser = jest.fn();
const mockedResourceIdentifier: Resource = {
    type: RESOURCE_TYPE.WORKSPACE,
    id: workspaceId,
};

jest.mock('../../../../../core/platform-utils/hooks/use-platform-utils.hook', () => ({
    ...jest.requireActual('../../../../../core/platform-utils/hooks/use-platform-utils.hook'),
    usePlatformUtils: jest.fn(() => ({
        useProductInfo: mockedUseProductInfo,
    })),
}));

jest.mock('../../../../../core/users/hook/use-users.hook', () => ({
    useResource: jest.fn(() => mockedResourceIdentifier),
    useUsers: jest.fn(() => ({
        useActiveUser: mockedUseActiveUser,
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => mockedWorkspaceIdentifier,
}));

describe('WorkspaceUserActions', () => {
    describe('Sass environment', () => {
        beforeEach(() => {
            mockedUseProductInfo.mockImplementation(() => ({ data: { environment: 'saas' } }));
        });

        it('Workspace contributor cannot edit and delete other member', async () => {
            mockedUseActiveUser.mockImplementation(() => ({
                data: mockedContributorUser,
                isPending: false,
            }));

            await render(
                <WorkspaceUserActions
                    activeUser={mockedContributorUser}
                    user={mockedWorkspaceAdminUser}
                    users={[mockedContributorUser, mockedWorkspaceAdminUser]}
                />
            );

            expect(
                screen.queryByRole('button', { name: `${mockedOrgAdminUser2.email} action menu` })
            ).not.toBeInTheDocument();
        });

        it('Workspace contributor can edit themselves (without role edition)', async () => {
            mockedUseActiveUser.mockImplementation(() => ({
                data: mockedContributorUser,
                isLoading: false,
            }));

            await render(
                <WorkspaceUserActions
                    activeUser={mockedContributorUser}
                    user={mockedContributorUser}
                    users={[mockedContributorUser, mockedWorkspaceAdminUser]}
                />
            );

            fireEvent.click(screen.getByRole('button', { name: `${mockedOrgAdminUser2.email} action menu` }));
            expect(screen.getByText('Edit')).toBeInTheDocument();
        });

        it('Check if organization admin cannot delete him/herself', async () => {
            mockedUseActiveUser.mockImplementation(() => ({
                data: mockedOrgAdminUser,
                isPending: false,
            }));

            await render(
                <WorkspaceUserActions
                    activeUser={mockedOrgAdminUser}
                    user={mockedOrgAdminUser}
                    users={[mockedOrgAdminUser]}
                />
            );

            const actionsMenu = screen.getByRole('button', { name: `${mockedOrgAdminUser.email} action menu` });
            expect(actionsMenu).toBeInTheDocument();
            fireEvent.click(actionsMenu);

            expect(screen.getByText('Edit')).toBeInTheDocument();
            expect(screen.queryByText('Delete')).not.toBeInTheDocument();
        });

        it('Check if edition and deletion is enabled when environment is of type SaaS', async () => {
            mockedUseActiveUser.mockImplementation(() => ({
                data: mockedOrgAdminUser,
                isPending: false,
            }));

            await render(
                <WorkspaceUserActions
                    activeUser={mockedOrgAdminUser}
                    user={mockedWorkspaceAdminUser}
                    users={[mockedOrgAdminUser, mockedWorkspaceAdminUser]}
                />
            );

            const actionsMenu = screen.getByRole('button', { name: `${mockedWorkspaceAdminUser.email} action menu` });
            expect(actionsMenu).toBeInTheDocument();
            fireEvent.click(actionsMenu);

            expect(screen.getByText('Edit')).toBeInTheDocument();
            expect(screen.getByText('Delete')).toBeInTheDocument();
        });

        it('Check if contributor cannot edit or delete other user - SaaS environment', async () => {
            mockedUseActiveUser.mockImplementation(() => ({
                data: mockedContributorUser,
                isPending: false,
            }));

            await render(
                <WorkspaceUserActions
                    activeUser={mockedContributorUser}
                    user={mockedContributorUser2}
                    users={[mockedContributorUser, mockedContributorUser2]}
                />
            );

            const actionsMenu = screen.queryByRole('button', { name: `${mockedContributorUser2.email} action menu` });
            expect(actionsMenu).not.toBeInTheDocument();
        });
    });

    it('Check if there is delete option when user is in INVITED status', async () => {
        mockedUseActiveUser.mockImplementation(() => ({
            data: mockedOrgAdminUser,
            isPending: false,
        }));

        await render(
            <WorkspaceUserActions
                activeUser={mockedOrgAdminUser}
                user={mockedInvitedUser}
                users={[mockedOrgAdminUser, mockedInvitedUser]}
            />
        );

        const actionsMenu = screen.getByRole('button', { name: `${mockedInvitedUser.email} action menu` });
        expect(actionsMenu).toBeInTheDocument();
        fireEvent.click(actionsMenu);

        expect(screen.getByText('Edit')).toBeInTheDocument();
        expect(screen.queryByText('Delete')).toBeInTheDocument();
    });

    it('Check if edition and deletion is enabled when environment is of type on-prem', async () => {
        mockedUseProductInfo.mockImplementation(() => ({ data: { environment: 'on-prem' } }));
        await render(
            <WorkspaceUserActions
                activeUser={mockedOrgAdminUser}
                user={mockedWorkspaceAdminUser}
                users={[mockedOrgAdminUser, mockedWorkspaceAdminUser]}
            />
        );

        const actionsMenu = screen.getByRole('button', { name: `${mockedWorkspaceAdminUser.email} action menu` });
        expect(actionsMenu).toBeInTheDocument();
        fireEvent.click(actionsMenu);

        expect(screen.getByText('Edit')).toBeInTheDocument();
        expect(screen.queryByText('Delete')).toBeInTheDocument();
    });

    it('Check if contributor cannot edit or delete other user - SaaS environment', async () => {
        mockedUseActiveUser.mockImplementation(() => ({
            data: mockedContributorUser,
            isPending: false,
        }));

        mockedUseProductInfo.mockImplementation(() => ({ data: { environment: 'saas' } }));
        await render(
            <WorkspaceUserActions
                activeUser={mockedContributorUser}
                user={mockedContributorUser2}
                users={[mockedContributorUser, mockedContributorUser2]}
            />
        );

        const actionsMenu = screen.queryByRole('button', { name: `${mockedContributorUser2.email} action menu` });
        expect(actionsMenu).not.toBeInTheDocument();
    });
});
