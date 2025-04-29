// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteQueryDTO } from '../../shared/dto/infinite-query.interface';

export enum AccountStatusDTO {
    REGISTERED = 'RGS', // organization was registered and is waiting for activation
    ACTIVE = 'ACT', // organization is active
    SUSPENDED = 'SSP', // organization is suspended
    DELETED = 'DEL', // organization was deleted
    REQUESTED_ACCESS = 'REQ', // organization requested access
}

export enum OrganizationTypeDTO {
    BUSINESS_TO_BUSINESS = 'B2B',
    BUSINESS_TO_CLIENT = 'B2C',
}

export interface OrganizationAdmin {
    firstName: string;
    lastName: string;
    email: string;
}

export interface OrganizationDTO {
    id: string;
    name: string;
    admins: OrganizationAdmin[];
    country: string;
    location: string;
    type: OrganizationTypeDTO;
    cellId: string;
    status: AccountStatusDTO;
    createdAt: string;
    createdBy: string;
    modifiedAt: string;
    modifiedBy: string;
    requestAccessReason: string;
}

export interface OrganizationsResponseDTO extends InfiniteQueryDTO {
    organizations: OrganizationDTO[];
    totalMatchedCount: number;
}

export interface GetOrganizationsQueryOptionsDTO extends Partial<Omit<OrganizationDTO, 'createdAt' | 'modifiedAt'>> {
    nextPage?: OrganizationsResponseDTO['nextPage'] | null;
    skip?: number;
    limit?: number;
    sortBy?: Extract<keyof OrganizationDTO, 'name' | 'createdAt' | 'status'>;
    createdAtFrom?: string;
    createdAtTo?: string;
    modifiedAtFrom?: string;
    modifiedAtTo?: string;
    sortDirection?: 'asc' | 'desc';
}
