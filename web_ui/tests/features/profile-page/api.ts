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

import { OpenApiRequest } from '../../../src/core/server/types';
import { ResourceTypeDTO, RoleResourceDTO, UserDTO, UserRoleDTO } from '../../../src/core/users/users.interface';
import { OpenApiFixtures } from '../../fixtures/open-api';
import { notFoundHandler } from '../../fixtures/open-api/setup-open-api-handlers';
import { getMockedMember, membersPayload } from './mocks';

type MembersPayload = typeof membersPayload;

const appendWorkspaceRole = (newRole: Pick<RoleResourceDTO, 'role' | 'resourceId'>, roles: RoleResourceDTO[]) => {
    if (
        roles.some((role) => {
            return role.role === newRole.role && role.resourceId === newRole.resourceId;
        })
    ) {
        return roles;
    }

    if (newRole.role === UserRoleDTO.ORGANIZATION_CONTRIBUTOR) {
        roles.push({
            role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
            resourceId: '128deb13-11ea-4dea-b050-8f8e308b7d8e',
            resourceType: ResourceTypeDTO.WORKSPACE,
        });

        return;
    }

    if (newRole.role === UserRoleDTO.ORGANIZATION_ADMIN) {
        roles.push({
            role: UserRoleDTO.WORKSPACE_ADMIN,
            resourceId: '128deb13-11ea-4dea-b050-8f8e308b7d8e',
            resourceType: ResourceTypeDTO.WORKSPACE,
        });
    }
};

const filterMembers = (
    req: OpenApiRequest<'User_find'>,
    inputMembersPayload: MembersPayload,
    inputMembers: UserDTO[]
): MembersPayload => {
    if (req.query.name) {
        const queryName = req.query.name;
        const members = inputMembersPayload.users.filter((member) => member.secondName.includes(queryName));

        return {
            users: members,
            nextPage: inputMembersPayload.nextPage,
            totalCount: inputMembersPayload.totalCount,
            totalMatchedCount: members.length,
        };
    }

    if (req.query.role && req.query.resourceType && req.query.resourceId) {
        const members = inputMembersPayload.users.filter((member) =>
            member.roles.some(
                (role) =>
                    role.role === req.query.role &&
                    role.resourceId === req.query.resourceId &&
                    role.resourceType === req.query.resourceType
            )
        );

        return {
            users: members,
            nextPage: inputMembersPayload.nextPage,
            totalCount: inputMembersPayload.totalCount,
            totalMatchedCount: members.length,
        };
    }

    return { ...inputMembersPayload, users: inputMembers };
};

export const registerApiMembers = ({
    registerApiResponse,
    openApi,
    inputMembersPayload = membersPayload,
}: {
    registerApiResponse: OpenApiFixtures['registerApiResponse'];
    openApi?: OpenApiFixtures['openApi'];
    inputMembersPayload?: MembersPayload;
}) => {
    const localMembersPayload = structuredClone(inputMembersPayload);

    let members = localMembersPayload.users;

    registerApiResponse('User_get_active_user', (_, res, ctx) => {
        // @ts-expect-error Issue in openapi types
        return res(ctx.json(members[0]));
    });

    registerApiResponse('User_find', (req, res, ctx) => {
        const newMembersPayload = filterMembers(req, localMembersPayload, members);

        members = [...newMembersPayload.users];

        return res(ctx.json(newMembersPayload));
    });

    registerApiResponse('UserStatus_change', async (req, res, ctx) => {
        members = members.filter((member) => member.id !== req.params.userId);

        return res(ctx.json({}));
    });

    registerApiResponse('User_modify', (req, res, ctx) => {
        // @ts-expect-error Issue in openapi types
        const newMember = getMockedMember(req.body);
        members = members.map((member) =>
            member.id === req.params.id
                ? {
                      ...member,
                      firstName: newMember.firstName,
                      secondName: newMember.secondName,
                  }
                : member
        );

        // @ts-expect-error Issue in openapi types
        return res(ctx.json(newMember));
    });

    openApi?.registerHandler('notFound', (context, res, ctx) => {
        if (context.request.path.endsWith('users/create')) {
            const newMemberRequest = structuredClone(context.request.body);
            delete newMemberRequest.password;

            const newMember = getMockedMember(newMemberRequest);

            members.push(newMember);

            return res(ctx.status(200), ctx.json(newMember));
        }

        if (context.request.path.includes('/membership') && context.request.path.includes('/roles')) {
            const newRole = context.request.body;

            members = members.map((member) => {
                if (member.id === context.request.params.id) {
                    const updatedRoles = member.roles.map((role) =>
                        role.resourceId === newRole.resourceId ? { ...role, role: newRole.role } : role
                    );

                    appendWorkspaceRole(newRole, updatedRoles);

                    return {
                        ...member,
                        roles: updatedRoles,
                    };
                }

                return member;
            });

            return res(ctx.status(200), ctx.json({}));
        }

        return notFoundHandler(context, res, ctx);
    });

    return {
        get() {
            return members;
        },
    };
};
