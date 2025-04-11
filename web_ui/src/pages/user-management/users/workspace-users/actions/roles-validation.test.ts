// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { RESOURCE_TYPE, USER_ROLE } from '../../../../../core/users/users.interface';
import { getMockedUser } from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { getAvailableRoles } from './roles-validation';

describe('roles-validation', () => {
    describe('getAvailableRoles', () => {
        const workspaceId = 'workspace-id';

        test('Returns no roles when active member is a workspace contributor', () => {
            const activeMemberContributor = getMockedUser({
                roles: [
                    {
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                        resourceId: workspaceId,
                    },
                ],
            });

            const members = [activeMemberContributor];

            expect(
                getAvailableRoles({
                    activeMember: activeMemberContributor,
                    members,
                    workspaceId,
                    isAccountOwner: true,
                })
            ).toEqual([]);
        });

        test('Returns no roles when there is only one user', () => {
            const activeMemberAdmin = getMockedUser({
                roles: [
                    {
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        role: USER_ROLE.WORKSPACE_ADMIN,
                        resourceId: workspaceId,
                    },
                ],
            });

            const users = [activeMemberAdmin];

            expect(
                getAvailableRoles({
                    activeMember: activeMemberAdmin,
                    members: users,
                    workspaceId,
                    isAccountOwner: true,
                })
            ).toEqual([]);
        });

        test('Returns no roles for active member as a workspace admin while editing themselves when there is only one workspace admin', () => {
            const activeMemberAdmin = getMockedUser({
                roles: [
                    {
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        role: USER_ROLE.WORKSPACE_ADMIN,
                        resourceId: workspaceId,
                    },
                ],
            });

            const members = [
                activeMemberAdmin,
                getMockedUser({
                    roles: [
                        {
                            resourceType: RESOURCE_TYPE.WORKSPACE,
                            role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                            resourceId: workspaceId,
                        },
                    ],
                }),
            ];

            expect(
                getAvailableRoles({ activeMember: activeMemberAdmin, members, workspaceId, isAccountOwner: true })
            ).toEqual([]);
        });

        test('Returns WORKSPACE_ADMIN and WORKSPACE_CONTRIBUTOR roles for active member as a workspace admin while editing workspace contributor', () => {
            const activeMemberAdmin = getMockedUser({
                roles: [
                    {
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        role: USER_ROLE.WORKSPACE_ADMIN,
                        resourceId: workspaceId,
                    },
                ],
            });

            const members = [
                activeMemberAdmin,
                getMockedUser({
                    roles: [
                        {
                            resourceType: RESOURCE_TYPE.WORKSPACE,
                            role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                            resourceId: workspaceId,
                        },
                    ],
                }),
            ];

            expect(
                getAvailableRoles({ activeMember: activeMemberAdmin, members, workspaceId, isAccountOwner: false })
            ).toEqual([USER_ROLE.WORKSPACE_ADMIN, USER_ROLE.WORKSPACE_CONTRIBUTOR]);
        });

        test('Returns WORKSPACE_ADMIN and WORKSPACE_CONTRIBUTOR roles when active member is a workspace admin and there are at least two admins', () => {
            const activeMemberAdmin = getMockedUser({
                roles: [
                    {
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        role: USER_ROLE.WORKSPACE_ADMIN,
                        resourceId: workspaceId,
                    },
                ],
            });

            const members = [
                activeMemberAdmin,
                getMockedUser({
                    roles: [
                        {
                            resourceType: RESOURCE_TYPE.WORKSPACE,
                            role: USER_ROLE.WORKSPACE_ADMIN,
                            resourceId: workspaceId,
                        },
                    ],
                }),
                getMockedUser({
                    roles: [
                        {
                            resourceType: RESOURCE_TYPE.WORKSPACE,
                            role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                            resourceId: workspaceId,
                        },
                    ],
                }),
            ];

            expect(
                getAvailableRoles({ activeMember: activeMemberAdmin, members, workspaceId, isAccountOwner: false })
            ).toEqual([USER_ROLE.WORKSPACE_ADMIN, USER_ROLE.WORKSPACE_CONTRIBUTOR]);
        });
    });
});
