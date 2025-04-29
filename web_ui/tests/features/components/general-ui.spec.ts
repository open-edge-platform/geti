// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { test } from '../../fixtures/base-test';

test.describe('General GUI Test', () => {
    test('Check if entry page is shown correctly.', async ({ page }) => {
        await page.goto('/');

        await expect(page.getByRole('tab', { name: 'Workspace 1' })).toBeVisible();
        await expect(page.getByText('Create new project')).toBeVisible();
    });

    test('Check if a max of 10 projects appears in the project list', async ({ page }) => {
        await page.goto('/');
        const projectsList = page.getByRole('list', { name: 'Projects in workspace' });
        const projectCount = await projectsList.getByRole('listitem').count();
        expect(projectCount).toBeLessThanOrEqual(10);
    });
});
