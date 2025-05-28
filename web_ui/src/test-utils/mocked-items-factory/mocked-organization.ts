// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OrganizationMetadata } from '@geti/core/src/users/services/onboarding-service.interface';
import { v4 as uuid } from 'uuid';

import {
    AccountStatusDTO,
    OrganizationDTO,
    OrganizationTypeDTO,
} from '../../core/organizations/dtos/organizations.interface';
import { AccountStatus, Organization, OrganizationType } from '../../core/organizations/organizations.interface';
import { getMockedAdminUser } from './mocked-users';

export const getMockedOrganization = (organization: Partial<Organization> = {}): Organization => {
    return {
        id: uuid(),
        name: 'Organization',
        admins: [getMockedAdminUser()],
        country: 'PLN',
        location: '',
        type: OrganizationType.BUSINESS_TO_BUSINESS,
        cellId: 'cellId',
        status: AccountStatus.ACTIVATED,
        createdAt: '2024-04-15T00:00:00Z',
        createdBy: '',
        modifiedAt: '',
        modifiedBy: '',
        requestAccessReason: '',
        ...organization,
    };
};

export const getMockedOrganizationDTO = (organization: Partial<OrganizationDTO> = {}): OrganizationDTO => {
    return {
        id: uuid(),
        name: 'Organization',
        admins: [getMockedAdminUser()],
        country: 'PLN',
        location: '',
        type: OrganizationTypeDTO.BUSINESS_TO_BUSINESS,
        cellId: 'cellId',
        status: AccountStatusDTO.ACTIVE,
        createdAt: '2024-04-15T00:00:00Z',
        createdBy: '',
        modifiedAt: '',
        modifiedBy: '',
        requestAccessReason: '',
        ...organization,
    };
};

export const getMockedOrganizationMetadata = (data: Partial<OrganizationMetadata> = {}): OrganizationMetadata => ({
    name: 'default',
    id: 'test-organization-id',
    status: AccountStatus.ACTIVATED,
    userStatus: AccountStatus.ACTIVATED,
    createdAt: '2024-09-11T09:17:42Z',
    ...data,
});
