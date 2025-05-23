// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { paths } from '@geti/core/src/services/routes';
import { test } from '../../fixtures/base-test';
import { project } from '../../mocks/segmentation/mocks';
import { registerUserApis } from './utils';

const WORKSPACE_ID = '61011e42d891c82e13ec92da';
const PROJECT_ID = project.id;
const USERS_URL = paths.project.users({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: WORKSPACE_ID,
    projectId: PROJECT_ID,
});

test.beforeEach(async ({ registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
        return res(ctx.status(200), ctx.json(project));
    });
});

test('Adding a new project contributor', async ({ page, registerApiResponse, projectUsersPage }) => {
    registerUserApis(registerApiResponse, 'admin@intel.com');

    await page.goto(USERS_URL);
    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('progressbar')).toBeHidden();

    const email = 'test@intel.com';
    const role = 'Project contributor';
    await projectUsersPage.addUser(email, role);

    const row = await projectUsersPage.getUserRow('User, Test');

    await expect(row).toBeVisible();
    await expect(row.getByRole('gridcell', { name: email })).toBeVisible();
    await expect(row.getByRole('gridcell', { name: role })).toBeVisible();
});

test('Removing a project contributor', async ({ page, registerApiResponse, projectUsersPage }) => {
    registerUserApis(registerApiResponse, 'admin@intel.com');

    await page.goto(USERS_URL);
    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('progressbar')).toBeHidden();

    const email = 'test2@intel.com';
    await projectUsersPage.removeUser('User 2, Test');

    await expect(page.getByRole('alertdialog')).toBeHidden();
    await expect(page.getByRole('rowheader', { name: new RegExp(email) })).toBeHidden();
});

test('Changing a project contributor to project manager', async ({ page, registerApiResponse, projectUsersPage }) => {
    registerUserApis(registerApiResponse, 'admin@intel.com');

    await page.goto(USERS_URL);

    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('progressbar')).toBeHidden();

    const email = 'User 2, Test';
    await projectUsersPage.editUser(email, 'Project manager');

    const row = await projectUsersPage.getUserRow(email);
    await expect(row.getByRole('gridcell', { name: 'Project manager' })).toBeVisible();
});

test('As a workspace contributor removing oneself from the project', async ({
    page,
    registerApiResponse,
    projectUsersPage,
}) => {
    registerUserApis(registerApiResponse, 'test2@intel.com');

    await page.goto(USERS_URL);

    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('progressbar')).toBeHidden();

    const email = 'User 2, Test';
    await projectUsersPage.removeUser(email);

    await expect(page).toHaveURL(
        paths.workspace({ organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633', workspaceId: WORKSPACE_ID })
    );
});

test('As a workspace admin removing oneself from the project', async ({
    page,
    registerApiResponse,
    projectUsersPage,
}) => {
    const email = 'admin@intel.com';
    registerUserApis(registerApiResponse, email);

    await page.goto(USERS_URL);

    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('progressbar')).toBeHidden();

    await projectUsersPage.removeUser('admin, admin');

    await expect(page.getByRole('row', { name: new RegExp('admin, admin') })).toBeHidden();
});

test('Searching for a user', async ({ page, registerApiResponse, projectUsersPage }) => {
    registerUserApis(registerApiResponse, 'admin@intel.com');

    await page.goto(USERS_URL);

    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('progressbar')).toBeHidden();

    const admin = page.getByText(/admin, admin/);

    await expect(admin).toBeVisible();
    await projectUsersPage.search('test');

    const user2 = await projectUsersPage.getUserRow('User 2, Test');
    await expect(user2).toBeVisible();
    await expect(page.getByText(/admin, admin/)).toBeHidden();

    await projectUsersPage.search(null);
    await expect(page.getByText(/admin, admin/)).toBeVisible();
});
