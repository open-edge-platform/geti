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

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { ForgotPasswordDTO, ResetPasswordDTO, UpdatePasswordDTO, UserRegistrationDTO } from '../dtos/members.interface';
import { RolesResponseDTO, UpdateRolesDTO, UserDTO, UsersResponseDTO } from '../users.interface';
import { UsersService } from './users-service.interface';
import {
    getMemberRoleDTO,
    getRoleCreationPayload,
    getRolesEntity,
    getUserDTO,
    getUserEntity,
    getUsersResponse,
    ROLE_OPERATION_MAPPING_DTO,
    USER_RESOURCE_TYPE_MAPPING_DTO,
} from './utils';

export const createApiUsersService: CreateApiService<UsersService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getUsers: UsersService['getUsers'] = async (orgId, queryParams) => {
        const { data } = await platformInstance.get<UsersResponseDTO>(router.USERS(orgId), { params: queryParams });

        return getUsersResponse(data);
    };

    const getUser: UsersService['getUser'] = async (orgId, userId) => {
        const { data } = await platformInstance.get<UserDTO>(router.USER(orgId, userId));

        return getUserEntity(data);
    };

    const getActiveUser: UsersService['getActiveUser'] = async (organizationId) => {
        const { data: activeUser } = await platformInstance.get<UserDTO>(router.ACTIVE_USER(organizationId));

        return getUserEntity(activeUser);
    };

    const createUser: UsersService['createUser'] = async (orgId, user) => {
        const { data } = await platformInstance.post<UserDTO>(router.CREATE_USER(orgId), user);

        return getUserEntity(data);
    };

    const updateUser: UsersService['updateUser'] = async (orgId, user) => {
        const { data } = await platformInstance.put<UserDTO>(router.USER(orgId, user.id), getUserDTO(user));

        return getUserEntity(data);
    };

    const updateUserStatuses: UsersService['updateUserStatuses'] = async (orgId, userId, newStatus) => {
        const requestBody = { organizationId: orgId, status: newStatus };

        await platformInstance.put(router.USER_STATUSES(orgId, userId), requestBody);
    };

    const inviteUser: UsersService['inviteUser'] = async (organizationId, email, userRoles) => {
        const roles = userRoles.map(getRoleCreationPayload);

        const user = {
            email,
            organizationId,
        };

        await platformInstance.post(router.INVITE_USER(organizationId), {
            user,
            roles,
        });
    };

    const uploadUserPhoto: UsersService['uploadUserPhoto'] = async (orgId, userId, userPhoto) => {
        const userPhotoFormData = new FormData();
        userPhotoFormData.set('photo_file', userPhoto);

        await platformInstance.post(router.USER_PHOTO(orgId, userId), userPhoto, {
            headers: {
                'content-type': 'multipart/form-data',
            },
        });
    };

    const deleteUserPhoto: UsersService['deleteUserPhoto'] = async (orgId, userId) => {
        await platformInstance.delete(router.USER_PHOTO(orgId, userId));
    };

    const getRoles: UsersService['getRoles'] = async (orgId, userId, resourceType) => {
        const { data } = await platformInstance.get<RolesResponseDTO>(
            router.USER_ROLES_RESOURCE(orgId, userId, USER_RESOURCE_TYPE_MAPPING_DTO[resourceType])
        );

        return getRolesEntity(data);
    };

    const updateRoles: UsersService['updateRoles'] = async (orgId, userId, roles) => {
        const rolesDTO: UpdateRolesDTO = {
            roles: roles.map(({ role, operation }) => ({
                role,
                operation: ROLE_OPERATION_MAPPING_DTO[operation],
            })),
        };

        await platformInstance.put(router.USER_ROLES(orgId, userId), { roles: rolesDTO.roles });
    };

    const updateMemberRole: UsersService['updateMemberRole'] = async (organizationId, memberId, memberRole) => {
        const roleDTO = getMemberRoleDTO(memberRole);

        await platformInstance.post(router.MEMBERSHIP.ROLES(organizationId, memberId), roleDTO);
    };

    const deleteMemberRole: UsersService['deleteMemberRole'] = async (organizationId, memberId, memberRole) => {
        await platformInstance.delete(
            router.MEMBERSHIP.DELETE_ROLE(organizationId, memberId, getMemberRoleDTO(memberRole))
        );
    };

    const registerMember: UsersService['registerMember'] = async (body: UserRegistrationDTO): Promise<void> => {
        await platformInstance.post(router.USER_REGISTRATION, body);
    };

    const forgotPassword: UsersService['forgotPassword'] = async (body: ForgotPasswordDTO): Promise<void> => {
        await platformInstance.post(router.FORGOT_PASSWORD, body);
    };

    const resetPassword: UsersService['resetPassword'] = async (body: ResetPasswordDTO): Promise<void> => {
        await platformInstance.post(router.RESET_PASSWORD, body);
    };

    const updatePassword: UsersService['updatePassword'] = async (passwords: UpdatePasswordDTO): Promise<void> => {
        const { uid, old_password, new_password } = passwords;

        await platformInstance.post(router.UPDATE_PASSWORD(uid), { new_password, old_password });
    };

    return {
        getUsers,
        getUser,
        getActiveUser,
        updateUser,
        updateUserStatuses,
        createUser,
        inviteUser,

        uploadUserPhoto,
        deleteUserPhoto,

        getRoles,
        updateRoles,

        updateMemberRole,
        deleteMemberRole,

        forgotPassword,
        registerMember,
        resetPassword,
        updatePassword,
    };
};
