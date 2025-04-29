// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatusDTO } from '../organizations/dtos/organizations.interface';
import { AccountStatus } from '../organizations/organizations.interface';
import { InfiniteQueryDTO } from '../shared/dto/infinite-query.interface';
import { QueryParametersDTO } from '../shared/dto/query-parameters';
import { InfiniteQuery } from '../shared/infinite-query.interface';
import { QueryParameters } from '../shared/query-parameters';
import { WorkspaceEntity } from '../workspaces/services/workspaces.interface';

export interface UserDTO {
    id: string;
    firstName: string;
    secondName: string;
    email: string;
    userPhoto?: string | null;
    externalId: string; // Identifier from the external identity system
    country: string;
    status: AccountStatusDTO;
    organizationId: string;
    organizationStatus: AccountStatusDTO;
    lastSuccessfulLogin: string | null;
    createdAt: string | null;
    currentSuccessfulLogin: string | null;
    createdBy: string;
    modifiedAt: string | null;
    modifiedBy: string | null;
    roles: RoleResourceDTO[];
    telemetryConsentAt?: string | null;
    userConsentAt?: string | null;
    userConsent?: string | null;
    presignedUrl?: string;
    lastLogoutDate?: string | null;
}

export interface UserCreationDTO {
    firstName: string;
    secondName: string;
    email: string;
    password: string;
    roles: RoleResourceDTO[];
}

export interface UsersResponseDTO extends InfiniteQueryDTO {
    users: UserDTO[];
    totalMatchedCount: number;
}

export const enum ResourceTypeDTO {
    WORKSPACE = 'workspace',
    PROJECT = 'project',
    ORGANIZATION = 'organization',
}

export const enum UserRoleDTO {
    WORKSPACE_ADMIN = 'workspace_admin',
    WORKSPACE_CONTRIBUTOR = 'workspace_contributor',
    ORGANIZATION_ADMIN = 'organization_admin',
    ORGANIZATION_CONTRIBUTOR = 'organization_contributor',
    PROJECT_MANAGER = 'project_manager',
    PROJECT_CONTRIBUTOR = 'project_contributor',
}

export enum RoleOperationDTO {
    CREATE = 'CREATE',
    TOUCH = 'TOUCH',
    DELETE = 'DELETE',
}

export interface RoleResourceDTO {
    role: UserRoleDTO;
    resourceType: ResourceTypeDTO;
    resourceId: string;
}

export interface RolesResponseDTO {
    roles: RoleResourceDTO[];
}

export interface UpdateRolesDTO {
    roles: {
        role: RoleResourceDTO;
        operation: RoleOperationDTO;
    }[];
}

export enum RESOURCE_TYPE {
    WORKSPACE = 'workspace',
    PROJECT = 'project',
    ORGANIZATION = 'organization',
}

export interface Resource {
    type: RESOURCE_TYPE;
    id: string;
}

export interface Role {
    role: USER_ROLE;
    resourceId: string;
    resourceType: RESOURCE_TYPE;
}

export enum USER_ROLE {
    WORKSPACE_ADMIN = 'Admin',
    WORKSPACE_CONTRIBUTOR = 'Contributor',
    PROJECT_MANAGER = 'Project manager',
    PROJECT_CONTRIBUTOR = 'Project contributor',
    ORGANIZATION_ADMIN = 'Organization admin',
    ORGANIZATION_CONTRIBUTOR = 'Organization contributor',
}

export interface UsersQueryParamsDTO
    extends Partial<
            Omit<
                UserDTO,
                | 'createdAt'
                | 'modifiedAt'
                | 'lastSuccessfulLogin'
                | 'organizationId'
                | 'organizationStatus'
                | 'userPhoto'
            >
        >,
        Partial<RoleResourceDTO>,
        QueryParametersDTO<keyof UserDTO> {
    lastSuccessfulLoginFrom?: string;
    lastSuccessfulLoginTo?: string;
}

export type WorkspaceRole = {
    role: USER_ROLE.WORKSPACE_ADMIN | USER_ROLE.WORKSPACE_CONTRIBUTOR;
    workspace: WorkspaceEntity;
};

export enum RoleOperation {
    CREATE = 'CREATE',
    TOUCH = 'TOUCH',
    DELETE = 'DELETE',
}

export interface RoleResource {
    role: USER_ROLE;
    resourceType: RESOURCE_TYPE;
    resourceId: string;
}

export interface UpdateRolePayload {
    role: RoleResourceDTO;
    operation: RoleOperationDTO;
}

export interface User {
    id: string;
    firstName: string;
    lastName: string;
    email: string;
    userPhoto: string | null;
    userConsent?: string | null;
    externalIdentitySystemId: string;
    country: string;
    status: AccountStatus;
    organizationId: string;
    organizationStatus: AccountStatus;
    lastSuccessfulLogin: string | null;
    currentSuccessfulLogin: string | null;
    createdAt: string | null;
    createdBy: string;
    modifiedAt: string | null;
    modifiedBy: string | null;
    roles: RoleResource[];
    /**
     * @deprecated Use roles in combination with useCheckPermission instead
     */
    isAdmin: boolean;
}

export interface UsersResponse extends InfiniteQuery {
    users: User[];
    totalMatchedCount: number;
}

export interface UsersQueryParams
    extends Partial<
            Omit<
                User,
                | 'createdAt'
                | 'modifiedAt'
                | 'lastSuccessfulLogin'
                | 'organizationId'
                | 'organizationStatus'
                | 'userPhoto'
            > & { name: string }
        >,
        Partial<RoleResource>,
        QueryParameters<keyof User> {
    lastSuccessfulLoginFrom?: string;
    lastSuccessfulLoginTo?: string;
}

export interface MemberRoleDTO {
    role: UserRoleDTO;
    resourceId: string;
}

export interface MemberRole {
    role: USER_ROLE;
    resourceId: string;
}
