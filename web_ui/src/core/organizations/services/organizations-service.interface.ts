// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
