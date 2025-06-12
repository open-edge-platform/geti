// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useUsers } from '@geti/core/src/users/hook/use-users.hook';
import { RESOURCE_TYPE, USER_ROLE } from '@geti/core/src/users/users.interface';
import { screen } from '@testing-library/react';
import { useParams } from 'react-router-dom';

import { WorkspacesConfig } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { getMockedUser } from '../../../test-utils/mocked-items-factory/mocked-users';
import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { useDefaultWorkspace } from '../../landing-page/workspaces-tabs/use-default-workspace.hook';
import { Workspaces } from './workspaces.component';

jest.mock('../../../providers/workspaces-provider/workspaces-provider.component', () => ({
    ...jest.requireActual('../../../providers/workspaces-provider/workspaces-provider.component'),
    useWorkspaces: jest.fn(),
}));

jest.mock('@geti/core/src/users/hook/use-users.hook', () => ({
    useUsers: jest.fn(() => ({
        useGetUserQuery: jest.fn(),
        useActiveUser: jest.fn(),
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({})),
}));

jest.mock('../../landing-page/workspaces-tabs/use-default-workspace.hook', () => ({
    useDefaultWorkspace: jest.fn(),
}));

jest.mock('../../../core/user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../../core/user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(),
}));

jest.mock('../../landing-page/workspaces-tabs/use-default-workspace.hook', () => ({
    useDefaultWorkspace: jest.fn(),
}));

describe('Workspaces', () => {
    const mockedWorkspace = getMockedWorkspace({ id: '1', name: 'Workspace 1' });
    const mockedWorkspace2 = getMockedWorkspace({ id: '2', name: 'Workspace 2' });

    it('Check if there are two workspaces displayed', async () => {
        const mockedWorkspaces = [mockedWorkspace, mockedWorkspace2];

        jest.mocked(useWorkspaces).mockReturnValue({
            workspaceId: '1',
            workspaces: mockedWorkspaces,
        });

        jest.mocked(useDefaultWorkspace).mockReturnValue({
            defaultWorkspaceId: undefined,
            reorderedWorkspaces: mockedWorkspaces,
        });

        jest.mocked(useUserGlobalSettings).mockReturnValue({
            saveConfig: jest.fn(),
            isSavingConfig: false,
            config: {} as WorkspacesConfig,
        });
        // @ts-expect-error We only care about data property
        jest.mocked(useUsers).mockReturnValue({ useActiveUser: () => ({ data: getMockedUser() }) });

        render(<Workspaces />);

        expect(screen.getByText('Workspace 1')).toBeInTheDocument();
        expect(screen.getByText('Workspace 2')).toBeInTheDocument();
    });

    it('Check if add workspace button is visible when user is organization contributor - FEATURE_FLAG_WORKSPACE_ACTIONS on', async () => {
        const organizationId = 'organization-id';
        jest.mocked(useParams).mockReturnValue({ organizationId });

        jest.mocked(useWorkspaces).mockReturnValue({
            workspaceId: '1',
            workspaces: [],
        });

        const mockedContributorUser = getMockedUser({
            roles: [
                {
                    resourceType: RESOURCE_TYPE.ORGANIZATION,
                    resourceId: organizationId,
                    role: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
                },
            ],
        });

        // @ts-expect-error We only care about data property
        jest.mocked(useUsers).mockReturnValue({ useActiveUser: () => ({ data: mockedContributorUser }) });

        render(<Workspaces />, { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: true } });
        expect(screen.getByRole('button', { name: 'Create new workspace' })).toBeInTheDocument();
    });

    it('Check if add workspace button is visible when user is organization admin - FEATURE_FLAG_WORKSPACE_ACTIONS on', async () => {
        const organizationId = 'organization-id';
        jest.mocked(useParams).mockReturnValue({ organizationId });
        jest.mocked(useWorkspaces).mockReturnValue({
            workspaceId: '1',
            workspaces: [],
        });

        const mockedAdminUser = getMockedUser({
            roles: [
                {
                    resourceId: organizationId,
                    resourceType: RESOURCE_TYPE.ORGANIZATION,
                    role: USER_ROLE.ORGANIZATION_ADMIN,
                },
            ],
        });
        // @ts-expect-error We only care about data property
        jest.mocked(useUsers).mockReturnValue({ useActiveUser: () => ({ data: mockedAdminUser }) });

        render(<Workspaces />, { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: true } });
        expect(screen.getByRole('button', { name: 'Create new workspace' })).toBeInTheDocument();
    });

    it('Check if add workspace button is not visible when user is not organization user - FEATURE_FLAG_WORKSPACE_ACTIONS on', async () => {
        const organizationId = 'organization-id';
        jest.mocked(useParams).mockReturnValue({ organizationId });
        jest.mocked(useWorkspaces).mockReturnValue({
            workspaceId: '1',
            workspaces: [],
        });

        const mockedUserFromOutsideTheOrg = getMockedUser({
            roles: [],
        });
        // @ts-expect-error We only care about data property
        jest.mocked(useUsers).mockReturnValue({ useActiveUser: () => ({ data: mockedUserFromOutsideTheOrg }) });

        render(<Workspaces />, { featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: true } });
        expect(screen.queryByRole('button', { name: 'Create new workspace' })).not.toBeInTheDocument();
    });
});
