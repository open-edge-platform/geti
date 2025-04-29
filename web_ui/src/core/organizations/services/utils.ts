// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RESOURCE_TYPE, Role, USER_ROLE } from '../../users/users.interface';
import {
    AccountStatusDTO,
    GetOrganizationsQueryOptionsDTO,
    OrganizationDTO,
    OrganizationsResponseDTO,
    OrganizationTypeDTO,
} from '../dtos/organizations.interface';
import {
    AccountStatus,
    Organization,
    OrganizationInvitationPayload,
    OrganizationsResponse,
    OrganizationType,
} from '../organizations.interface';
import { GetOrganizationsQueryOptions } from './organizations-service.interface';

const ORGANIZATION_TYPES_MAPPER: Record<OrganizationTypeDTO, OrganizationType> = {
    [OrganizationTypeDTO.BUSINESS_TO_BUSINESS]: OrganizationType.BUSINESS_TO_BUSINESS,
    [OrganizationTypeDTO.BUSINESS_TO_CLIENT]: OrganizationType.BUSINESS_TO_CLIENT,
};

const ORGANIZATION_TYPES_MAPPER_DTO: Record<OrganizationType, OrganizationTypeDTO> = {
    [OrganizationType.BUSINESS_TO_BUSINESS]: OrganizationTypeDTO.BUSINESS_TO_BUSINESS,
    [OrganizationType.BUSINESS_TO_CLIENT]: OrganizationTypeDTO.BUSINESS_TO_CLIENT,
};

export const ORGANIZATION_STATUS_MAPPER: Record<AccountStatusDTO, AccountStatus> = {
    [AccountStatusDTO.SUSPENDED]: AccountStatus.SUSPENDED,
    [AccountStatusDTO.ACTIVE]: AccountStatus.ACTIVATED,
    [AccountStatusDTO.DELETED]: AccountStatus.DELETED,
    [AccountStatusDTO.REGISTERED]: AccountStatus.INVITED,
    [AccountStatusDTO.REQUESTED_ACCESS]: AccountStatus.REQUESTED_ACCESS,
};

export const ORGANIZATION_STATUS_MAPPER_DTO: Record<AccountStatus, AccountStatusDTO> = {
    [AccountStatus.SUSPENDED]: AccountStatusDTO.SUSPENDED,
    [AccountStatus.ACTIVATED]: AccountStatusDTO.ACTIVE,
    [AccountStatus.DELETED]: AccountStatusDTO.DELETED,
    [AccountStatus.INVITED]: AccountStatusDTO.REGISTERED,
    [AccountStatus.REQUESTED_ACCESS]: AccountStatusDTO.REQUESTED_ACCESS,
};

export const getOrganizationEntity = (organization: OrganizationDTO): Organization => {
    const {
        id,
        country,
        cellId,
        createdBy,
        createdAt,
        type,
        modifiedAt,
        modifiedBy,
        status,
        name,
        location,
        admins,
        requestAccessReason,
    } = organization;

    return {
        id,
        name,
        admins,
        cellId,
        country,
        location,
        createdBy,
        createdAt,
        modifiedBy,
        modifiedAt,
        requestAccessReason,
        type: ORGANIZATION_TYPES_MAPPER[type],
        status: ORGANIZATION_STATUS_MAPPER[status],
    };
};

export const getOrganizationsEntity = (organizationResponse: OrganizationsResponseDTO): OrganizationsResponse => {
    const { organizations, totalCount, totalMatchedCount, nextPage } = organizationResponse;

    return {
        organizations: organizations.map(getOrganizationEntity),
        totalCount,
        totalMatchedCount,
        nextPage: nextPage.limit > 0 ? nextPage : null,
    };
};

export const getOrganizationsEntityDTO = (organization: Organization): OrganizationDTO => {
    const {
        id,
        country,
        cellId,
        createdBy,
        createdAt,
        type,
        modifiedAt,
        modifiedBy,
        status,
        name,
        location,
        admins,
        requestAccessReason,
    } = organization;

    return {
        id,
        name,
        admins,
        cellId,
        country,
        location,
        createdBy,
        createdAt,
        modifiedBy,
        modifiedAt,
        requestAccessReason,
        type: ORGANIZATION_TYPES_MAPPER_DTO[type],
        status: ORGANIZATION_STATUS_MAPPER_DTO[status],
    };
};

export const getOrganizationsQueryOptionsDTO = (
    queryOptions: GetOrganizationsQueryOptions
): GetOrganizationsQueryOptionsDTO => {
    let newQueryOptions: GetOrganizationsQueryOptionsDTO = {};

    const { type, status, sortDirection } = queryOptions;

    newQueryOptions = {
        ...queryOptions,
        type: type ? ORGANIZATION_TYPES_MAPPER_DTO[type] : undefined,
        status: status ? ORGANIZATION_STATUS_MAPPER_DTO[status] : undefined,
        sortDirection: sortDirection ? (sortDirection === 'ASC' ? 'asc' : 'desc') : undefined,
    };

    return newQueryOptions;
};

export const getOrganizationInvitationPayload = (
    organizationName: string,
    adminEmail: string
): OrganizationInvitationPayload => {
    return {
        organizationData: {
            name: organizationName,
        },
        adminData: {
            email: adminEmail,
        },
    };
};

export const getApplicationAdminRole = (workspaceId: string): Role[] => [getWorkspaceAdminRole(workspaceId)];

const getWorkspaceAdminRole = (workspaceId: string): Role => ({
    role: USER_ROLE.WORKSPACE_ADMIN,
    resourceId: workspaceId,
    resourceType: RESOURCE_TYPE.WORKSPACE,
});
