// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
