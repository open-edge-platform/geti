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

import { v4 as uuid } from 'uuid';

import { USER_ROLE, WorkspaceRole } from '../../../src/core/users/users.interface';
import { expect } from '../../fixtures/base-test';
import { MembersPage } from '../../fixtures/page-objects/members-page';
import { test } from '../fixtures';

const expectMemberToBeVisible = async (
    membersPage: MembersPage,
    member: { email: string; firstName: string; lastName: string; role: WorkspaceRole['role'] }
) => {
    const memberRow = membersPage.getMemberRow(member.email);

    await expect(membersPage.getEmailCell(member.email, memberRow)).toBeVisible();
    await expect(membersPage.getNameCell(member.firstName, member.lastName, memberRow)).toBeVisible();
    await expect(membersPage.getRoleCell(member.role, memberRow)).toBeVisible();
};

const expectMemberNotToBeVisible = async (
    membersPage: MembersPage,
    member: { email: string; firstName: string; lastName: string; role: WorkspaceRole['role'] }
) => {
    await expect(membersPage.getMemberRow(member.email)).toBeHidden();
};

test.describe('Members management suite', () => {
    const workspaceAdminMember = {
        email: `test-admin-${uuid()}@intel.com`,
        firstName: 'Test',
        lastName: 'Admin',
        password: 'Test1234',
        role: USER_ROLE.WORKSPACE_ADMIN,
    } as const;

    const workspaceContributorMember = {
        email: `test-contributor-${uuid()}@intel.com`,
        firstName: 'Test',
        lastName: 'Contributor',
        password: 'Test1234',
        role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
    } as const;

    test.afterEach(async ({ membersPage }, testInfo) => {
        if (testInfo.status !== 'passed') {
            console.info('Cleanup');
            await membersPage.removeMember(workspaceAdminMember.email);
            await membersPage.removeMember(workspaceContributorMember.email);
        }
    });

    test('Members management', { tag: ['@daily'] }, async ({ membersPage, page }) => {
        await page.route('**/api/v1/product_info', async (route) => {
            const response = await route.fetch();
            const body = await response.json();
            body['smtp-defined'] = 'False';

            await route.fulfill({
                status: 200,
                body: JSON.stringify(body),
            });
        });

        await membersPage.open();

        await test.step('Creates new workspace admin and workspace contributor member', async () => {
            await membersPage.addMember(workspaceContributorMember);

            await expectMemberToBeVisible(membersPage, workspaceContributorMember);

            await membersPage.addMember(workspaceAdminMember);

            await expectMemberToBeVisible(membersPage, workspaceAdminMember);
        });

        await test.step('Filters by workspace admin and workspace contributor role', async () => {
            await membersPage.filterByRole(USER_ROLE.WORKSPACE_ADMIN);

            await expectMemberToBeVisible(membersPage, workspaceAdminMember);
            await expectMemberNotToBeVisible(membersPage, workspaceContributorMember);

            await membersPage.filterByRole(USER_ROLE.WORKSPACE_CONTRIBUTOR);

            await expectMemberToBeVisible(membersPage, workspaceContributorMember);
            await expectMemberNotToBeVisible(membersPage, workspaceAdminMember);

            await membersPage.filterByRole('All role');
            await expectMemberToBeVisible(membersPage, workspaceAdminMember);
            await expectMemberToBeVisible(membersPage, workspaceContributorMember);
        });

        await test.step("Filters by member's name and email", async () => {
            await membersPage.filterByNameOrEmail(workspaceAdminMember.email);

            await expectMemberToBeVisible(membersPage, workspaceAdminMember);
            await expectMemberNotToBeVisible(membersPage, workspaceContributorMember);

            await membersPage.filterByNameOrEmail(workspaceContributorMember.lastName);

            await expectMemberToBeVisible(membersPage, workspaceContributorMember);
            await expectMemberNotToBeVisible(membersPage, workspaceAdminMember);

            await membersPage.resetSearchFilter();
        });

        await test.step('Edits workspace admin and workspace contributor member', async () => {
            const updatedWorkspaceAdminMember = {
                ...workspaceAdminMember,
                firstName: 'Updated',
                lastName: 'Old Admin',
                role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
            } as const;

            await membersPage.editMember(updatedWorkspaceAdminMember);

            await expectMemberToBeVisible(membersPage, updatedWorkspaceAdminMember);

            const updatedWorkspaceContributorMember = {
                ...workspaceContributorMember,
                firstName: 'Updated',
                lastName: 'Old Contributor',
                role: USER_ROLE.WORKSPACE_ADMIN,
            } as const;

            await membersPage.editMember(updatedWorkspaceContributorMember);

            await expectMemberToBeVisible(membersPage, updatedWorkspaceContributorMember);
        });

        await test.step('Removes workspace admin and workspace contributor member', async () => {
            await membersPage.removeMember(workspaceContributorMember.email);

            await expectMemberNotToBeVisible(membersPage, workspaceContributorMember);

            await membersPage.removeMember(workspaceAdminMember.email);

            await expectMemberNotToBeVisible(membersPage, workspaceAdminMember);
        });
    });
});
