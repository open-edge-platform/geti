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

import { SortDirection } from '../../../shared/components/table/table.interface';
import { GetOrganizationsQueryOptionsDTO } from '../dtos/organizations.interface';
import { Organization, OrganizationsResponse } from '../organizations.interface';

export interface GetOrganizationsQueryOptions extends Partial<Omit<Organization, 'createdAt' | 'modifiedAt'>> {
    skip?: number;
    limit?: number;
    sortBy?: Extract<keyof Organization, 'name' | 'createdAt' | 'status'>;
    createdAtFrom?: string;
    createdAtTo?: string;
    modifiedAtFrom?: string;
    modifiedAtTo?: string;
    sortDirection?: SortDirection;
}

export interface OrganizationsService {
    getOrganizations: (queryOptions: GetOrganizationsQueryOptionsDTO) => Promise<OrganizationsResponse>;
    getOrganization: (id: string) => Promise<Organization>;
    deleteOrganization: (id: string) => Promise<void>;
    updateOrganization: (organization: Organization) => Promise<Organization>;
    inviteOrganization: (organizationName: string, adminEmail: string) => Promise<void>;
}
