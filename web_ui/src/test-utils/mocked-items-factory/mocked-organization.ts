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

import { v4 as uuid } from 'uuid';

import {
    AccountStatusDTO,
    OrganizationDTO,
    OrganizationTypeDTO,
} from '../../core/organizations/dtos/organizations.interface';
import { AccountStatus, Organization, OrganizationType } from '../../core/organizations/organizations.interface';
import { OrganizationMetadata } from '../../core/users/services/onboarding-service.interface';
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
