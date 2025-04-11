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

import { UseMutationResult, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { AccountStatusDTO } from '../../organizations/dtos/organizations.interface';
import {
    MemberRole,
    Resource,
    RESOURCE_TYPE,
    Role,
    RoleResource,
    UpdateRolePayload,
    User,
    UserCreationDTO,
    UsersQueryParams,
} from '../users.interface';

export interface UseGetUsersQuery {
    users: User[];
    totalCount: number;
    totalMatchedCount: number;
    isLoading: boolean;
    isSuccess: boolean;
    isFetchingNextPage: boolean;
    isError: boolean;
    getNextPage: () => Promise<void>;
}

interface UseUsersBasePayload {
    organizationId: string;
    userId: string;
}

export interface UseInviteUserPayload {
    organizationId: string;
    email: string;
    roles: Role[];
}

export interface UseCreateUserPayload {
    organizationId: string;
    user: UserCreationDTO;
}

export interface UseUpdateUserPayload extends UseUsersBasePayload {
    user: User;
}

export interface UseUpdateUserStatusesPayload extends UseUsersBasePayload {
    status: AccountStatusDTO;
}

export type UseDeletePhotoUserPayload = UseUsersBasePayload;

export interface UseDeleteUserPayload extends Omit<UseUsersBasePayload, 'userId'> {
    user: User;
}

export interface UseUploadUserPhotoPayload extends UseUsersBasePayload {
    userPhoto: File;
}

export type UseDeleteUserPhotoPayload = UseUsersBasePayload;

export interface UseUserRoles extends UseUsersBasePayload {
    resourceType: RESOURCE_TYPE;
}

export interface UseUpdateUserRolesPayload extends UseUsersBasePayload {
    newRoles: UpdateRolePayload[];
}

interface UseUpdateMemberRolePayload {
    organizationId: string;
    memberId: string;
    role: MemberRole;
}

export interface UseUsers {
    useActiveUser: (organizationId: string, resource?: Resource) => UseQueryResult<User, AxiosError>;
    useGetUsersQuery: (organizationId: string, queryParams?: UsersQueryParams) => UseGetUsersQuery;
    useGetUserQuery: (organizationId: string, userId: string | undefined) => UseQueryResult<User, AxiosError>;
    useCreateUser: () => UseMutationResult<User, AxiosError, UseCreateUserPayload>;
    useUpdateUser: () => UseMutationResult<User, AxiosError, UseUpdateUserPayload>;
    useUpdateUserStatuses: () => UseMutationResult<void, AxiosError, UseUpdateUserStatusesPayload>;
    useDeleteUser: () => UseMutationResult<void, AxiosError, UseDeleteUserPayload>;
    useUploadUserPhoto: () => UseMutationResult<void, AxiosError, UseUploadUserPhotoPayload>;
    useDeleteUserPhoto: () => UseMutationResult<void, AxiosError, UseDeletePhotoUserPayload>;
    useUserRoles: (args: UseUserRoles) => UseQueryResult<RoleResource[], AxiosError>;
    useUpdateUserRoles: () => UseMutationResult<void, AxiosError, UseUpdateUserRolesPayload>;
    useInviteUserMutation: (organizationId: string) => UseMutationResult<void, AxiosError, UseInviteUserPayload>;

    useUpdateMemberRole: () => UseMutationResult<void, AxiosError, UseUpdateMemberRolePayload>;
    useDeleteMemberRole: () => UseMutationResult<void, AxiosError, UseUpdateMemberRolePayload>;
}
