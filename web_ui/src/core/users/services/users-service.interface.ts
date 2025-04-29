// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatusDTO } from '../../organizations/dtos/organizations.interface';
import { ForgotPasswordDTO, ResetPasswordDTO, UpdatePasswordDTO, UserRegistrationDTO } from '../dtos/members.interface';
import {
    MemberRole,
    Resource,
    RESOURCE_TYPE,
    Role,
    RoleResource,
    UpdateRolePayload,
    User,
    UserCreationDTO,
    UsersQueryParamsDTO,
    UsersResponse,
} from '../users.interface';

export interface UsersService {
    getUsers: (orgId: string, queryParams: UsersQueryParamsDTO) => Promise<UsersResponse>;
    getUser: (orgId: string, userId: string) => Promise<User>;
    getActiveUser: (organizationId: string, resource?: Resource) => Promise<User>;
    createUser: (orgId: string, user: UserCreationDTO) => Promise<User>;
    updateUser: (orgId: string, user: User) => Promise<User>;
    updateUserStatuses: (orgId: string, userId: string, status: AccountStatusDTO) => Promise<void>;
    inviteUser: (orgId: string, email: string, roles: Role[]) => Promise<void>;

    uploadUserPhoto: (orgId: string, userId: string, userPhoto: File) => Promise<void>;
    deleteUserPhoto: (orgId: string, userId: string) => Promise<void>;

    updateRoles: (orgId: string, userId: string, roles: UpdateRolePayload[]) => Promise<void>;
    getRoles: (orgId: string, userId: string, resourceType: RESOURCE_TYPE) => Promise<RoleResource[]>;

    updateMemberRole: (organizationId: string, memberId: string, role: MemberRole) => Promise<void>;
    deleteMemberRole: (organizationId: string, memberId: string, role: MemberRole) => Promise<void>;

    registerMember: (body: UserRegistrationDTO) => Promise<void>;
    forgotPassword: (body: ForgotPasswordDTO) => Promise<void>;
    resetPassword: (body: ResetPasswordDTO) => Promise<void>;
    updatePassword: (passwords: UpdatePasswordDTO) => Promise<void>;
}
