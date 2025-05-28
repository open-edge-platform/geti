// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedUser } from '../../../../../src/test-utils/mocked-items-factory/mocked-users';
import { UsersService } from './users-service.interface';
import { getRoleEntity } from './utils';

export const createInMemoryUsersService = (): UsersService => {
    const getActiveUser: UsersService['getActiveUser'] = async (_organizationId) => {
        return getMockedUser();
    };

    const getUser: UsersService['getUser'] = async (_organizationId) => {
        return getMockedUser();
    };

    const getUsers: UsersService['getUsers'] = async () => {
        return Promise.resolve({
            users: [],
            totalCount: 2,
            totalMatchedCount: 1,
            nextPage: {
                skip: 2,
                limit: 10,
            },
        });
    };

    const createUser: UsersService['createUser'] = async (_orgId, user) => {
        const mockedUser = getMockedUser({
            firstName: user.firstName,
            email: user.email,
            lastName: user.secondName,
            roles: user.roles.map(getRoleEntity),
        });
        return mockedUser;
    };

    const updateUser: UsersService['updateUser'] = async (_orgId, user) => {
        return getMockedUser(user);
    };

    const updateUserStatuses: UsersService['updateUserStatuses'] = async (_orgId, _userId, _status) => {
        return;
    };

    const inviteUser: UsersService['inviteUser'] = async (_orgId, _email) => {
        await Promise.resolve();
    };

    const uploadUserPhoto: UsersService['uploadUserPhoto'] = async (_orgId, _userId, _userPhoto) => {
        await Promise.resolve();
    };

    const deleteUserPhoto: UsersService['deleteUserPhoto'] = async (_orgId, _userId) => {
        await Promise.resolve();
    };

    const getRoles: UsersService['getRoles'] = async (_orgId, _userId, _resourceType) => {
        return Promise.resolve([]);
    };

    const updateRoles: UsersService['updateRoles'] = async (_orgId, _userId, _roles) => {
        await Promise.resolve();
    };

    const updateMemberRole: UsersService['updateMemberRole'] = async (_orgId, _memberId, _role) => {
        await Promise.resolve();
    };

    const deleteMemberRole: UsersService['deleteMemberRole'] = async (_orgId, _memberId, _role) => {
        await Promise.resolve();
    };

    const registerMember: UsersService['registerMember'] = async (): Promise<void> => {
        return Promise.resolve();
    };

    const forgotPassword: UsersService['forgotPassword'] = async (): Promise<void> => {
        return Promise.resolve();
    };

    const resetPassword: UsersService['resetPassword'] = async (): Promise<void> => {
        return Promise.resolve();
    };

    const updatePassword: UsersService['updatePassword'] = async (): Promise<void> => {
        await Promise.resolve();
    };

    return {
        getActiveUser,
        getUser,
        getUsers,
        createUser,
        updateUser,
        updateUserStatuses,
        inviteUser,

        uploadUserPhoto,
        deleteUserPhoto,

        getRoles,
        updateRoles,

        updateMemberRole,
        deleteMemberRole,

        registerMember,
        resetPassword,
        updatePassword,
        forgotPassword,
    };
};
