// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
