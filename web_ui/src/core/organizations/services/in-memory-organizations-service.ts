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

import { getMockedOrganization } from '../../../test-utils/mocked-items-factory/mocked-organization';
import { AccountStatus, Organization, OrganizationType } from '../organizations.interface';
import { OrganizationsService } from './organizations-service.interface';

export const createInMemoryOrganizationsService = (): OrganizationsService => {
    const getOrganizations: OrganizationsService['getOrganizations'] = () => {
        return Promise.resolve({
            organizations: [
                getMockedOrganization({
                    createdAt: '',
                    createdBy: 'test@intel.com',
                    cellId: '',
                    country: 'PL',
                    location: 'PL',
                    modifiedAt: '',
                    modifiedBy: '',
                    name: '',
                    admins: [],
                    status: AccountStatus.ACTIVATED,
                    type: OrganizationType.BUSINESS_TO_BUSINESS,
                    id: '123',
                }),
            ],
            totalCount: 1,
            totalMatchedCount: 1,
            nextPage: {
                skip: 0,
                limit: 0,
            },
        });
    };

    const getOrganization: OrganizationsService['getOrganization'] = () => {
        return Promise.resolve(
            getMockedOrganization({
                createdAt: '',
                createdBy: 'test@intel.com',
                cellId: '',
                country: 'PL',
                location: 'PL',
                modifiedAt: '',
                modifiedBy: '',
                name: '',
                admins: [],
                status: AccountStatus.ACTIVATED,
                type: OrganizationType.BUSINESS_TO_BUSINESS,
                id: '123',
            })
        );
    };

    const deleteOrganization: OrganizationsService['deleteOrganization'] = (_id: string) => {
        return Promise.resolve();
    };

    const updateOrganization: OrganizationsService['updateOrganization'] = (_organization: Organization) => {
        return Promise.resolve(
            getMockedOrganization({
                createdAt: '',
                createdBy: 'test@intel.com',
                cellId: '',
                country: 'PL',
                location: 'PL',
                modifiedAt: '',
                modifiedBy: '',
                name: '',
                admins: [],
                status: AccountStatus.ACTIVATED,
                type: OrganizationType.BUSINESS_TO_BUSINESS,
                id: '123',
            })
        );
    };

    const inviteOrganization = (_organizationName: string, _adminEmail: string) => {
        return Promise.resolve();
    };

    return {
        getOrganizations,
        getOrganization,
        updateOrganization,
        deleteOrganization,
        inviteOrganization,
    };
};
