// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { createInMemoryUsersService } from '@geti/core/src/users/services/in-memory-users-service';
import { getUserEntity } from '@geti/core/src/users/services/utils';
import { RESOURCE_TYPE, ResourceTypeDTO, UserDTO, UserRoleDTO } from '@geti/core/src/users/users.interface';
import { renderHook, waitFor } from '@testing-library/react';
import { useParams } from 'react-router-dom';

import { AccountStatusDTO } from '../../../core/organizations/dtos/organizations.interface';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { useCheckPermission } from './has-permission.component';
import { OPERATION_OLD } from './has-permission.interface';

jest.mock('react-router-dom', () => ({ ...jest.requireActual('react-router-dom'), useParams: jest.fn() }));

const resources = {
    workspaceOne: '97f438a6-6857-4516-bc24-2b2066798ff7',
    workspaceTwo: 'a5ccf719-c2a3-4e7f-b15e-e566683cb15f',
    workspaceThree: 'df73e72f-8ae8-45ac-8a28-7cb5649aa429',
    projectOne: '66e16033d9f1a2bd4bc79777',
    organizationOne: '2ce1ebe4-a9f9-4fa9-af0a-fb37003f781d',
    organizationTwo: '92c26091-c318-451e-a46e-69f3d78cb145',
    organizationThree: 'a02a6b4b-7de1-48f3-936b-e25da529d1f0',
};
const userDTO: UserDTO = {
    id: 'ae5b1daf-eee8-492c-b274-b599a56e0420',
    firstName: 'firstName',
    secondName: 'secondName',
    email: 'test@test.com',
    status: AccountStatusDTO.ACTIVE,
    organizationId: '92c26091-c318-451e-a46e-69f3d78cb145',
    organizationStatus: AccountStatusDTO.ACTIVE,
    externalId: '',
    country: '',
    createdAt: '',
    createdBy: '',
    modifiedAt: '',
    modifiedBy: '',
    roles: [
        {
            role: UserRoleDTO.WORKSPACE_ADMIN,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: resources.workspaceOne,
        },
        {
            role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: resources.workspaceOne,
        },
        {
            role: UserRoleDTO.WORKSPACE_ADMIN,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: resources.workspaceTwo,
        },
        {
            role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: resources.workspaceTwo,
        },
        {
            role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: resources.workspaceThree,
        },
        {
            role: UserRoleDTO.PROJECT_MANAGER,
            resourceType: ResourceTypeDTO.PROJECT,
            resourceId: resources.projectOne,
        },
        {
            role: UserRoleDTO.ORGANIZATION_ADMIN,
            resourceType: ResourceTypeDTO.ORGANIZATION,
            resourceId: resources.organizationOne,
        },
        {
            role: UserRoleDTO.ORGANIZATION_ADMIN,
            resourceType: ResourceTypeDTO.ORGANIZATION,
            resourceId: resources.organizationTwo,
        },
        {
            role: UserRoleDTO.ORGANIZATION_ADMIN,
            resourceType: ResourceTypeDTO.ORGANIZATION,
            resourceId: resources.organizationThree,
        },
        {
            role: UserRoleDTO.WORKSPACE_ADMIN,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: resources.workspaceThree,
        },
    ],
    lastSuccessfulLogin: '2024-09-17T08:32:17Z',
    currentSuccessfulLogin: null,
};

const wrapper = ({ children }: { children?: ReactNode }) => {
    const usersService = createInMemoryUsersService();
    usersService.getActiveUser = () => Promise.resolve(getUserEntity(userDTO));

    return <RequiredProviders usersService={usersService}>{children}</RequiredProviders>;
};

describe('useCheckPermission', () => {
    beforeEach(() => {
        jest.mocked(useParams).mockReturnValue({ workspaceId: undefined });
    });

    describe('project creation', () => {
        it('workspace params does not match user roles', async () => {
            jest.mocked(useParams).mockReturnValue({ workspaceId: '111111' });
            const { result } = renderHook(() => useCheckPermission([OPERATION_OLD.PROJECT_CREATION]), {
                wrapper,
            });

            await waitFor(() => {
                expect(result.current).toBe(false);
            });
        });

        it('workspace params match user roles', async () => {
            jest.mocked(useParams).mockReturnValue({ workspaceId: resources.workspaceThree });
            const { result } = renderHook(() => useCheckPermission([OPERATION_OLD.PROJECT_CREATION]), {
                wrapper,
            });

            await waitFor(() => {
                expect(result.current).toBe(true);
            });
        });

        it('workspace resources match user roles', async () => {
            const { result } = renderHook(
                () =>
                    useCheckPermission(
                        [OPERATION_OLD.PROJECT_CREATION],
                        [{ type: RESOURCE_TYPE.WORKSPACE, id: resources.workspaceThree }]
                    ),
                { wrapper }
            );

            await waitFor(() => {
                expect(result.current).toBe(true);
            });
        });
    });
});
