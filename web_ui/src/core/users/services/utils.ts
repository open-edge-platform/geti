// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatusDTO } from '../../organizations/dtos/organizations.interface';
import { AccountStatus } from '../../organizations/organizations.interface';
import {
    getApplicationAdminRole,
    ORGANIZATION_STATUS_MAPPER,
    ORGANIZATION_STATUS_MAPPER_DTO,
} from '../../organizations/services/utils';
import {
    MemberRole,
    RESOURCE_TYPE,
    ResourceTypeDTO,
    Role,
    RoleOperation,
    RoleOperationDTO,
    RoleResource,
    RoleResourceDTO,
    RolesResponseDTO,
    UpdateRolePayload,
    User,
    USER_ROLE,
    UserDTO,
    UserRoleDTO,
    UsersQueryParams,
    UsersQueryParamsDTO,
    UsersResponse,
    UsersResponseDTO,
} from '../users.interface';

const USER_STATUS_MAPPING_DTO: Record<AccountStatus, AccountStatusDTO> = {
    [AccountStatus.ACTIVATED]: AccountStatusDTO.ACTIVE,
    [AccountStatus.INVITED]: AccountStatusDTO.REGISTERED,
    [AccountStatus.SUSPENDED]: AccountStatusDTO.SUSPENDED,
    [AccountStatus.DELETED]: AccountStatusDTO.DELETED,
    [AccountStatus.REQUESTED_ACCESS]: AccountStatusDTO.REQUESTED_ACCESS,
};

export const USER_STATUS_MAPPING: Record<AccountStatusDTO, AccountStatus> = {
    [AccountStatusDTO.ACTIVE]: AccountStatus.ACTIVATED,
    [AccountStatusDTO.REGISTERED]: AccountStatus.INVITED,
    [AccountStatusDTO.SUSPENDED]: AccountStatus.SUSPENDED,
    [AccountStatusDTO.DELETED]: AccountStatus.DELETED,
    [AccountStatusDTO.REQUESTED_ACCESS]: AccountStatus.REQUESTED_ACCESS,
};

const USER_RESOURCE_TYPE_MAPPING: Record<ResourceTypeDTO, RESOURCE_TYPE> = {
    [ResourceTypeDTO.PROJECT]: RESOURCE_TYPE.PROJECT,
    [ResourceTypeDTO.WORKSPACE]: RESOURCE_TYPE.WORKSPACE,
    [ResourceTypeDTO.ORGANIZATION]: RESOURCE_TYPE.ORGANIZATION,
};

export const USER_RESOURCE_TYPE_MAPPING_DTO: Record<RESOURCE_TYPE, ResourceTypeDTO> = {
    [RESOURCE_TYPE.PROJECT]: ResourceTypeDTO.PROJECT,
    [RESOURCE_TYPE.WORKSPACE]: ResourceTypeDTO.WORKSPACE,
    [RESOURCE_TYPE.ORGANIZATION]: ResourceTypeDTO.ORGANIZATION,
};

export const ROLE_OPERATION_MAPPING_DTO: Record<RoleOperation, RoleOperationDTO> = {
    [RoleOperation.CREATE]: RoleOperationDTO.CREATE,
    [RoleOperation.TOUCH]: RoleOperationDTO.TOUCH,
    [RoleOperation.DELETE]: RoleOperationDTO.DELETE,
};
export const USER_ROLE_MAPPING: Record<UserRoleDTO, USER_ROLE> = {
    [UserRoleDTO.WORKSPACE_ADMIN]: USER_ROLE.WORKSPACE_ADMIN,
    [UserRoleDTO.WORKSPACE_CONTRIBUTOR]: USER_ROLE.WORKSPACE_CONTRIBUTOR,
    [UserRoleDTO.PROJECT_MANAGER]: USER_ROLE.PROJECT_MANAGER,
    [UserRoleDTO.PROJECT_CONTRIBUTOR]: USER_ROLE.PROJECT_CONTRIBUTOR,
    [UserRoleDTO.ORGANIZATION_ADMIN]: USER_ROLE.ORGANIZATION_ADMIN,
    [UserRoleDTO.ORGANIZATION_CONTRIBUTOR]: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
};

const USER_ROLE_MAPPING_DTO: Record<USER_ROLE, UserRoleDTO> = {
    [USER_ROLE.WORKSPACE_ADMIN]: UserRoleDTO.WORKSPACE_ADMIN,
    [USER_ROLE.WORKSPACE_CONTRIBUTOR]: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
    [USER_ROLE.PROJECT_CONTRIBUTOR]: UserRoleDTO.PROJECT_CONTRIBUTOR,
    [USER_ROLE.PROJECT_MANAGER]: UserRoleDTO.PROJECT_MANAGER,
    [USER_ROLE.ORGANIZATION_ADMIN]: UserRoleDTO.ORGANIZATION_ADMIN,
    [USER_ROLE.ORGANIZATION_CONTRIBUTOR]: UserRoleDTO.ORGANIZATION_CONTRIBUTOR,
};

const resourceMapDTO: Record<ResourceTypeDTO, RESOURCE_TYPE> = {
    [ResourceTypeDTO.PROJECT]: RESOURCE_TYPE.PROJECT,
    [ResourceTypeDTO.WORKSPACE]: RESOURCE_TYPE.WORKSPACE,
    [ResourceTypeDTO.ORGANIZATION]: RESOURCE_TYPE.ORGANIZATION,
};

const getRoles = (roles: RoleResourceDTO[]): RoleResource[] => {
    return roles.reduce<Role[]>((prev, curr) => {
        const { resourceId, resourceType, role } = curr;

        if (USER_ROLE_MAPPING[role] === USER_ROLE.WORKSPACE_ADMIN) {
            return [...prev, ...getApplicationAdminRole(resourceId)];
        }

        return [...prev, { role: USER_ROLE_MAPPING[role], resourceId, resourceType: resourceMapDTO[resourceType] }];
    }, []);
};

const getRolesDTO = (roles: RoleResource[]): RoleResourceDTO[] => {
    return roles.map(getRoleDTO);
};

export const getUserEntity = (user: UserDTO): User => {
    const {
        id,
        country,
        email,
        createdBy,
        createdAt,
        lastSuccessfulLogin,
        firstName,
        secondName,
        externalId,
        organizationId,
        organizationStatus,
        status,
        modifiedBy,
        modifiedAt,
        userPhoto,
        roles,
        currentSuccessfulLogin,
    } = user;

    // eslint-disable-next-line max-len
    // Note: Query invalidation was not working because the endpoint to delete the user returns only a portion of the user DTO. In this case the "roles" field is not returned, therefore the table would not render because the query would not fire.
    const rolesEntity = status === AccountStatusDTO.DELETED ? [] : getRoles(roles);

    return {
        id,
        country,
        email,
        organizationId,
        createdAt,
        createdBy,
        lastSuccessfulLogin,
        modifiedAt,
        modifiedBy,
        firstName,
        currentSuccessfulLogin,
        // TODO: remove ?? null statement when backend supports sending avatar
        userPhoto: userPhoto ?? null,
        lastName: secondName,
        externalIdentitySystemId: externalId,
        status: USER_STATUS_MAPPING[status],
        organizationStatus: ORGANIZATION_STATUS_MAPPER[organizationStatus],
        roles: rolesEntity,
        isAdmin: rolesEntity.some(({ role }) => role === USER_ROLE.WORKSPACE_ADMIN),
    };
};

export const getUserDTO = (user: User): UserDTO => {
    const {
        id,
        country,
        email,
        createdBy,
        createdAt,
        lastSuccessfulLogin,
        firstName,
        lastName,
        externalIdentitySystemId,
        organizationId,
        organizationStatus,
        status,
        modifiedBy,
        modifiedAt,
        userPhoto,
        roles,
        currentSuccessfulLogin,
    } = user;

    return {
        id,
        country,
        email,
        organizationId,
        createdAt,
        createdBy,
        lastSuccessfulLogin,
        modifiedAt,
        modifiedBy,
        firstName,
        userPhoto,
        currentSuccessfulLogin,
        secondName: lastName,
        externalId: externalIdentitySystemId,
        status: USER_STATUS_MAPPING_DTO[status],
        organizationStatus: ORGANIZATION_STATUS_MAPPER_DTO[organizationStatus],
        roles: getRolesDTO(roles),
    };
};

export const getUsersResponse = ({
    users,
    totalCount,
    nextPage,
    totalMatchedCount,
}: UsersResponseDTO): UsersResponse => {
    return {
        users: users.map((user) => getUserEntity(user)),
        totalCount,
        nextPage: nextPage.limit > 0 ? nextPage : null,
        totalMatchedCount,
    };
};

export const getUsersQueryParamsDTO = (queryParams: UsersQueryParams): UsersQueryParamsDTO => {
    const { sortDirection, status, lastName, externalIdentitySystemId, role, resourceType, sortBy, roles, ...rest } =
        queryParams;

    return {
        ...rest,
        status: status ? USER_STATUS_MAPPING_DTO[status] : undefined,
        secondName: lastName,
        externalId: externalIdentitySystemId,
        role: role ? USER_ROLE_MAPPING_DTO[role] : undefined,
        resourceType: resourceType ? USER_RESOURCE_TYPE_MAPPING_DTO[resourceType] : undefined,
        sortDirection: sortDirection ? (sortDirection === 'ASC' ? 'asc' : 'desc') : undefined,

        sortBy:
            sortBy === 'lastName'
                ? 'secondName'
                : sortBy === 'externalIdentitySystemId'
                  ? 'externalId'
                  : (sortBy as keyof UserDTO),
    };
};

export const getRoleEntity = ({ role, resourceType, resourceId }: RoleResourceDTO): RoleResource => ({
    resourceId,
    role: USER_ROLE_MAPPING[role],
    resourceType: USER_RESOURCE_TYPE_MAPPING[resourceType],
});

export const getRolesEntity = ({ roles }: RolesResponseDTO) => {
    return roles.map(getRoleEntity);
};

export const getRoleDTO = ({ role, resourceType, resourceId }: RoleResource): RoleResourceDTO => ({
    resourceId,
    role: USER_ROLE_MAPPING_DTO[role],
    resourceType: USER_RESOURCE_TYPE_MAPPING_DTO[resourceType],
});

export const getRoleCreationPayload = (role: RoleResource): UpdateRolePayload => ({
    role: getRoleDTO(role),
    operation: ROLE_OPERATION_MAPPING_DTO[RoleOperation.CREATE],
});

export const getRoleDeletionPayload = (role: RoleResource) => ({
    role: getRoleDTO(role),
    operation: ROLE_OPERATION_MAPPING_DTO[RoleOperationDTO.DELETE],
});

export const getMemberRoleDTO = ({ role, resourceId }: MemberRole) => ({
    role: USER_ROLE_MAPPING_DTO[role],
    resourceId,
});
