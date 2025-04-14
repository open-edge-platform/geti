// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { USER_ROLE_MAPPING } from '../../../src/core/users/services/utils';
import { ResourceTypeDTO, USER_ROLE, UserDTO, UserRoleDTO } from '../../../src/core/users/users.interface';
import { expect, test } from '../../fixtures/base-test';
import { MembersPage } from '../../fixtures/page-objects/members-page';
import { registerApiMembers } from './api';
import {
    getMockedMember,
    organizationId,
    workspace,
    workspaceAdmin1,
    workspaceAdmin2,
    workspaceContributor,
} from './mocks';

const expectMembersToBeVisible = async (
    membersPage: MembersPage,
    members: Pick<UserDTO, 'firstName' | 'secondName' | 'roles' | 'email'>[]
) => {
    for (const member of members) {
        const row = membersPage.getMemberRow(member.email);

        await expect(membersPage.getEmailCell(member.email, row)).toBeVisible();
        await expect(membersPage.getNameCell(member.firstName, member.secondName, row)).toBeVisible();

        const workspaceRole = member.roles.find((role) => role.resourceType === ResourceTypeDTO.WORKSPACE);
        if (workspaceRole === undefined) {
            throw new Error(`${member} does not have workspace role`);
        }

        await expect(membersPage.getRoleCell(USER_ROLE_MAPPING[workspaceRole.role], row)).toBeVisible();
    }
};

test.describe('Members page', () => {
    test.beforeEach(({ registerApiResponse, openApi }) => {
        registerApiResponse('GetProductInfo', async (_req, res, ctx) => {
            const { mock, status } = openApi.mockResponseForOperation('GetProductInfo');

            return res(ctx.status(status), ctx.json({ ...mock, 'smtp-defined': 'False' }));
        });

        registerApiResponse('Workspace_find', async (_req, res, ctx) => {
            return res(
                ctx.json({
                    workspaces: [workspace],
                    totalCount: 1,
                    totalMatchedCount: 1,
                    nextPage: {
                        skip: 0,
                        limit: 0,
                    },
                })
            );
        });
    });

    test('Creates a workspace admin member', async ({ page, membersPage, registerApiResponse, openApi }) => {
        const member = {
            firstName: 'Yet another',
            lastName: 'User',
            email: 'test50@intel.com',
            password: 'Test1234',
            role: USER_ROLE.WORKSPACE_ADMIN,
        } as const;

        const members = registerApiMembers({ registerApiResponse, openApi });

        await membersPage.openByURL(organizationId);

        await expect(membersPage.addMemberButton).toBeVisible();

        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());

        const addUserRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'POST' && req.url().includes('/users/create');
        });

        await membersPage.addMember(member);

        const addUserRequest = await addUserRequestPromise;
        const addUserRequestPayload = JSON.parse(addUserRequest.postData() ?? '');

        expect(addUserRequestPayload).toEqual({
            email: member.email,
            firstName: member.firstName,
            secondName: member.lastName,
            password: expect.any(String),
            roles: [
                {
                    role: 'organization_admin',
                    resourceType: 'organization',
                    resourceId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                },
                {
                    role: 'workspace_admin',
                    resourceType: 'workspace',
                    resourceId: workspace.id,
                },
            ],
        });

        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());
    });

    test('Creates a workspace contributor member', async ({ page, membersPage, openApi, registerApiResponse }) => {
        const member = {
            firstName: 'Test',
            lastName: 'User',
            email: 'tes@intel.com',
            password: 'Test1234',
            role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
        } as const;

        const members = registerApiMembers({ registerApiResponse, openApi });

        await membersPage.openByURL(organizationId);

        await expect(membersPage.addMemberButton).toBeVisible();
        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());

        const addUserRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'POST' && req.url().includes('/users/create');
        });

        await membersPage.addMember(member);

        const addUserRequest = await addUserRequestPromise;
        const addUserRequestPayload = JSON.parse(addUserRequest.postData() ?? '');

        expect(addUserRequestPayload).toEqual({
            email: member.email,
            firstName: member.firstName,
            secondName: member.lastName,
            password: expect.any(String),
            roles: [
                {
                    role: 'organization_contributor',
                    resourceType: 'organization',
                    resourceId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                },
                {
                    role: 'workspace_contributor',
                    resourceType: 'workspace',
                    resourceId: workspace.id,
                },
            ],
        });

        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());
    });

    test('Removes a workspace admin member', async ({ page, membersPage, registerApiResponse }) => {
        const members = registerApiMembers({ registerApiResponse });

        await membersPage.openByURL(organizationId);

        await expect(membersPage.membersTable).toBeVisible();
        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());

        const removeAdminUserRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'PUT' && req.url().includes(`/users/${workspaceAdmin2.id}/statuses`);
        });

        await membersPage.removeMember(workspaceAdmin2.email);

        const removeAdminUserRequest = await removeAdminUserRequestPromise;
        const removeAdminUserRequestPayload = JSON.parse(removeAdminUserRequest.postData() ?? '');

        expect(removeAdminUserRequestPayload).toEqual({
            organizationId,
            status: 'DEL',
        });

        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());
        await expect(membersPage.getEmailCell(workspaceAdmin2.email)).toBeHidden();
    });

    test('Removes a workspace contributor member', async ({ page, membersPage, registerApiResponse }) => {
        const members = registerApiMembers({ registerApiResponse });

        await membersPage.openByURL(organizationId);

        await expect(membersPage.membersTable).toBeVisible();
        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());

        const removeAdminUserRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'PUT' && req.url().includes(`/users/${workspaceContributor.id}/statuses`);
        });

        await membersPage.removeMember(workspaceContributor.email);

        const removeAdminUserRequest = await removeAdminUserRequestPromise;
        const removeAdminUserRequestPayload = JSON.parse(removeAdminUserRequest.postData() ?? '');

        expect(removeAdminUserRequestPayload).toEqual({
            organizationId,
            status: 'DEL',
        });

        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());
        await expect(membersPage.getEmailCell(workspaceContributor.email)).toBeHidden();
    });

    test('Filters by workspace admin or contributor role', async ({ page, membersPage, registerApiResponse }) => {
        const members = registerApiMembers({ registerApiResponse });

        await membersPage.openByURL(organizationId);

        await expect(membersPage.membersTable).toBeVisible();
        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());

        const filterMembersRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'GET' && req.url().includes(`/users`);
        });

        await membersPage.filterByRole(USER_ROLE.WORKSPACE_ADMIN);

        const filterMembersRequest = await filterMembersRequestPromise;

        expect(filterMembersRequest.url()).toContain(`role=${UserRoleDTO.WORKSPACE_ADMIN}`);

        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());
        await expect(membersPage.getEmailCell(workspaceContributor.email)).toBeHidden();

        const filterContributorMembersRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'GET' && req.url().includes(`/users`);
        });

        await membersPage.filterByRole(USER_ROLE.WORKSPACE_CONTRIBUTOR);

        const filterContributorMembersRequest = await filterContributorMembersRequestPromise;

        expect(filterContributorMembersRequest.url()).toContain(`role=${UserRoleDTO.WORKSPACE_CONTRIBUTOR}`);

        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);
        await expectMembersToBeVisible(membersPage, members.get());
        await expect(membersPage.getEmailCell(workspaceAdmin1.email)).toBeHidden();
        await expect(membersPage.getEmailCell(workspaceAdmin2.email)).toBeHidden();
    });

    test("Filters by member's name", async ({ page, membersPage, registerApiResponse }) => {
        const members = registerApiMembers({ registerApiResponse });

        await membersPage.openByURL(organizationId);

        await expect(membersPage.membersTable).toBeVisible();
        await expect(membersPage.membersTableCount).toHaveCount(members.get().length);

        const filterMembersRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'GET' && req.url().includes(`/users`);
        });

        await membersPage.filterByNameOrEmail(workspaceContributor.secondName);

        const filterMembersRequest = await filterMembersRequestPromise;

        expect(filterMembersRequest.url()).toContain(`name=${workspaceContributor.secondName}`);

        await expect(membersPage.membersTableCount).toHaveCount(1);
        await expectMembersToBeVisible(membersPage, members.get());
        await expect(membersPage.getEmailCell(workspaceAdmin1.email)).toBeHidden();
        await expect(membersPage.getEmailCell(workspaceAdmin2.email)).toBeHidden();
    });

    test.describe('FEATURE_FLAG_MANAGE_USERS_ROLES: on', () => {
        test.use({ featureFlags: { FEATURE_FLAG_MANAGE_USERS_ROLES: true } });

        test('Edits workspace admin user', async ({ page, membersPage, registerApiResponse, openApi }) => {
            const editedWorkspaceAdmin2 = getMockedMember({
                ...workspaceAdmin2,
                firstName: 'Edit Test',
                secondName: 'User',
                roles: [
                    {
                        role: UserRoleDTO.ORGANIZATION_CONTRIBUTOR,
                        resourceType: ResourceTypeDTO.ORGANIZATION,
                        resourceId: organizationId,
                    },
                ],
            });

            const members = registerApiMembers({ registerApiResponse, openApi });

            await membersPage.openByURL(organizationId);

            await expect(membersPage.membersTable).toBeVisible();

            const editMemberRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'PUT' && req.url().includes('/users');
            });

            const editMemberRolesRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'POST' && req.url().includes('/membership') && req.url().includes('/roles');
            });

            const editedMember = {
                email: editedWorkspaceAdmin2.email,
                firstName: editedWorkspaceAdmin2.firstName,
                lastName: editedWorkspaceAdmin2.secondName,
                role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
            } as const;

            await membersPage.editMember(editedMember);

            const editMemberRequest = await editMemberRequestPromise;
            const editMemberRolesRequest = await editMemberRolesRequestPromise;

            const editMemberRequestPayload = JSON.parse(editMemberRequest.postData() ?? '');
            const editMemberRolesRequestPayload = JSON.parse(editMemberRolesRequest.postData() ?? '');

            expect(editMemberRolesRequestPayload).toEqual({
                role: UserRoleDTO.ORGANIZATION_CONTRIBUTOR,
                resourceId: organizationId,
            });
            expect(editMemberRequestPayload).toEqual(editedWorkspaceAdmin2);

            await expectMembersToBeVisible(membersPage, members.get());
            await expect(membersPage.getNameCell(workspaceAdmin2.firstName, workspaceAdmin2.secondName)).toBeHidden();
        });

        test('Edits workspace contributor user', async ({ page, membersPage, registerApiResponse, openApi }) => {
            const editedWorkspaceContributor = getMockedMember({
                ...workspaceContributor,
                firstName: 'Test',
                secondName: 'User',
                roles: [
                    {
                        role: UserRoleDTO.ORGANIZATION_ADMIN,
                        resourceType: ResourceTypeDTO.ORGANIZATION,
                        resourceId: organizationId,
                    },
                ],
            });

            const members = registerApiMembers({ registerApiResponse, openApi });

            await membersPage.openByURL(organizationId);

            await expect(membersPage.membersTable).toBeVisible();

            const editMemberRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'PUT' && req.url().includes('/users');
            });

            const editMemberRolesRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'POST' && req.url().includes('/membership') && req.url().includes('/roles');
            });

            const editedMember = {
                email: editedWorkspaceContributor.email,
                firstName: editedWorkspaceContributor.firstName,
                lastName: editedWorkspaceContributor.secondName,
                role: USER_ROLE.WORKSPACE_ADMIN,
            } as const;

            await membersPage.editMember(editedMember);

            const editMemberRequest = await editMemberRequestPromise;
            const editMemberRolesRequest = await editMemberRolesRequestPromise;

            const editMemberRequestPayload = JSON.parse(editMemberRequest.postData() ?? '');
            const editMemberRolesRequestPayload = JSON.parse(editMemberRolesRequest.postData() ?? '');

            expect(editMemberRolesRequestPayload).toEqual({
                role: UserRoleDTO.ORGANIZATION_ADMIN,
                resourceId: organizationId,
            });
            expect(editMemberRequestPayload).toEqual(editedWorkspaceContributor);

            await expectMembersToBeVisible(membersPage, members.get());
            await expect(
                membersPage.getNameCell(workspaceContributor.firstName, workspaceContributor.secondName)
            ).toBeHidden();
        });
    });

    test.describe('FEATURE_FLAG_MANAGE_USERS_ROLES: off', () => {
        test.use({ featureFlags: { FEATURE_FLAG_MANAGE_USERS_ROLES: false } });

        test('Edits workspace admin user', async ({ page, membersPage, registerApiResponse }) => {
            const editedWorkspaceAdmin2 = getMockedMember({
                ...workspaceAdmin2,
                firstName: 'EditedTest',
                secondName: 'User',
                roles: [
                    {
                        role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
                        resourceType: ResourceTypeDTO.WORKSPACE,
                        resourceId: workspace.id,
                    },
                ],
            });

            const members = registerApiMembers({ registerApiResponse });

            await membersPage.openByURL(organizationId);

            await expect(membersPage.membersTable).toBeVisible();

            const editMemberRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'PUT' && req.url().includes('/users') && !req.url().includes('/roles');
            });

            const editMemberRolesRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'PUT' && req.url().includes('/users') && req.url().includes('/roles');
            });

            const editedMember = {
                email: editedWorkspaceAdmin2.email,
                firstName: editedWorkspaceAdmin2.firstName,
                lastName: editedWorkspaceAdmin2.secondName,
                role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
            } as const;

            await membersPage.editMember(editedMember);

            const editMemberRequest = await editMemberRequestPromise;
            const editMemberRolesRequest = await editMemberRolesRequestPromise;

            const editMemberRequestPayload = JSON.parse(editMemberRequest.postData() ?? '');
            const editMemberRolesRequestPayload = JSON.parse(editMemberRolesRequest.postData() ?? '');

            expect(editMemberRolesRequestPayload).toEqual({
                roles: [
                    {
                        operation: 'DELETE',
                        role: {
                            role: UserRoleDTO.WORKSPACE_ADMIN,
                            resourceType: ResourceTypeDTO.WORKSPACE,
                            resourceId: workspace.id,
                        },
                    },
                    {
                        operation: 'CREATE',
                        role: {
                            role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
                            resourceType: ResourceTypeDTO.WORKSPACE,
                            resourceId: workspace.id,
                        },
                    },
                ],
            });
            expect(editMemberRequestPayload).toEqual(editedWorkspaceAdmin2);

            await expectMembersToBeVisible(membersPage, members.get());
            await expect(membersPage.getNameCell(workspaceAdmin2.firstName, workspaceAdmin2.secondName)).toBeHidden();
        });

        test('Edits workspace contributor user', async ({ page, membersPage, registerApiResponse }) => {
            const editedWorkspaceContributor = getMockedMember({
                ...workspaceContributor,
                firstName: 'Test',
                secondName: 'User',
                roles: [
                    {
                        role: UserRoleDTO.WORKSPACE_ADMIN,
                        resourceType: ResourceTypeDTO.WORKSPACE,
                        resourceId: workspace.id,
                    },
                ],
            });

            const members = registerApiMembers({ registerApiResponse });

            await membersPage.openByURL(organizationId);

            await expect(membersPage.membersTable).toBeVisible();

            const editMemberRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'PUT' && req.url().includes('/users') && !req.url().includes('/roles');
            });

            const editMemberRolesRequestPromise = page.waitForRequest((req) => {
                return req.method() === 'PUT' && req.url().includes('/users') && req.url().includes('/roles');
            });

            const editedMember = {
                email: editedWorkspaceContributor.email,
                firstName: editedWorkspaceContributor.firstName,
                lastName: editedWorkspaceContributor.secondName,
                role: USER_ROLE.WORKSPACE_ADMIN,
            } as const;

            await membersPage.editMember(editedMember);

            const editMemberRequest = await editMemberRequestPromise;
            const editMemberRolesRequest = await editMemberRolesRequestPromise;

            const editMemberRequestPayload = JSON.parse(editMemberRequest.postData() ?? '');
            const editMemberRolesRequestPayload = JSON.parse(editMemberRolesRequest.postData() ?? '');

            expect(editMemberRolesRequestPayload).toEqual({
                roles: [
                    {
                        operation: 'DELETE',
                        role: {
                            role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
                            resourceType: ResourceTypeDTO.WORKSPACE,
                            resourceId: workspace.id,
                        },
                    },
                    {
                        operation: 'CREATE',
                        role: {
                            role: UserRoleDTO.WORKSPACE_ADMIN,
                            resourceType: ResourceTypeDTO.WORKSPACE,
                            resourceId: workspace.id,
                        },
                    },
                ],
            });
            expect(editMemberRequestPayload).toEqual(editedWorkspaceContributor);

            await expectMembersToBeVisible(membersPage, members.get());
            await expect(
                membersPage.getNameCell(workspaceContributor.firstName, workspaceContributor.secondName)
            ).toBeHidden();
        });
    });
});
