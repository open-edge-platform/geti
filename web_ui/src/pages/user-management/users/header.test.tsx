// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { Environment, GPUProvider } from '../../../core/platform-utils/dto/utils.interface';
import { createInMemoryPlatformUtilsService } from '../../../core/platform-utils/services/create-in-memory-platform-utils-service';
import { Resource, RESOURCE_TYPE } from '../../../core/users/users.interface';
import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { getMockedWorkspaceIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import {
    getMockedAdminUser,
    getMockedOrganizationAdminUser,
} from '../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { Header } from './header.component';

const { workspaceId, organizationId } = getMockedWorkspaceIdentifier();
const mockedOrgAdminUser = getMockedOrganizationAdminUser({ id: 'user-admin-id' }, workspaceId, organizationId);
const mockedWorkspaceAdminUser = getMockedAdminUser(
    {
        id: 'user-workspace-admin-id',
    },
    workspaceId
);

const mockedUseActiveUser = jest.fn();
const mockedGetUsersQuery = jest.fn();
const mockedUseProductInfo = jest.fn();

const mockedResourceIdentifier: Resource = {
    type: RESOURCE_TYPE.WORKSPACE,
    id: workspaceId,
};

jest.mock('../../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(() => true),
}));

jest.mock('../../../core/users/hook/use-users.hook', () => ({
    useResource: jest.fn(() => mockedResourceIdentifier),
    useUsers: jest.fn(() => ({
        useGetUsersQuery: mockedGetUsersQuery,
        useActiveUser: mockedUseActiveUser,
        useInviteUserMutation: jest.fn(),
        useCreateUser: jest.fn(),
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

describe('Users table header', () => {
    beforeEach(() => {
        mockedGetUsersQuery.mockImplementation(() => ({
            data: [mockedOrgAdminUser, mockedWorkspaceAdminUser],
        }));
        mockedUseProductInfo.mockImplementation(() => ({ data: { environment: 'saas' } }));
        mockedUseActiveUser.mockImplementation(() => ({
            data: mockedWorkspaceAdminUser,
            isPending: false,
        }));
    });

    afterEach(() => {
        mockedGetUsersQuery.mockReset();
        mockedUseProductInfo.mockReset();
        mockedUseActiveUser.mockReset();
    });

    it('Check if Invite User button is visible on saas environment', async () => {
        await render(<Header />);
        expect(screen.getByRole('button', { name: 'Send invite' })).toBeInTheDocument();
    });

    it('Do not show add user button when environment is saas ', async () => {
        await render(<Header />);
        expect(screen.queryByRole('button', { name: 'Add user' })).not.toBeInTheDocument();
    });

    it('Show add user button when environment is on-prem and email server is off', async () => {
        jest.mocked(useIsSaasEnv).mockImplementation(() => false);

        const platformUtilsService = createInMemoryPlatformUtilsService();
        platformUtilsService.getProductInfo = async () => {
            return {
                productVersion: '1.6.0',
                buildVersion: '1.6.0.test.123123',
                intelEmail: 'support@geti.com',
                isSmtpDefined: false,
                grafanaEnabled: false,
                environment: Environment.ON_PREM,
                gpuProvider: GPUProvider.INTEL,
            };
        };
        await render(<Header />, { services: { platformUtilsService } });
        expect(await screen.findByRole('button', { name: 'Add user' })).toBeInTheDocument();
    });

    it('Do not show add user button when environment is on-prem and email server is on', async () => {
        jest.mocked(useIsSaasEnv).mockImplementation(() => false);

        const platformUtilsService = createInMemoryPlatformUtilsService();
        platformUtilsService.getProductInfo = async () => {
            return {
                productVersion: '1.6.0',
                buildVersion: '1.6.0.test.123123',
                intelEmail: 'support@geti.com',
                isSmtpDefined: true,
                grafanaEnabled: false,
                environment: Environment.ON_PREM,
                gpuProvider: GPUProvider.INTEL,
            };
        };
        await render(<Header />, { services: { platformUtilsService } });

        expect(screen.queryByRole('button', { name: 'Add user' })).not.toBeInTheDocument();
    });
});
