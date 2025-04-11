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

import { expect, Page } from '@playwright/test';

import { RunTestDialogPage } from './run-test-dialog-page';
import { ProjectTestPage } from './test-page';

const EXPECTED_TESTING_TIME = 3 * 60 * 1000; // 3 minutes

export class ProjectTestsPage {
    constructor(private page: Page) {}

    async runTest() {
        await this.page.getByRole('button', { name: /run test/i }).click();

        return new RunTestDialogPage(this.page);
    }

    async waitForTestToFinish(test: string) {
        const name = new RegExp(test, 'i');
        const row = this.page.getByRole('row', { name });
        await expect(row).toBeVisible();

        await expect(row.getByLabel(/model score value/i)).toBeVisible({ timeout: EXPECTED_TESTING_TIME });
    }

    async gotoTest(test: string) {
        const name = new RegExp(test, 'i');
        const row = this.page.getByRole('row', { name });
        await row.click();

        return new ProjectTestPage(this.page);
    }

    async deleteTest(name: string) {
        const row = this.page.getByRole('row', { name });

        await expect(row).toBeVisible();
        const openMenu = row.getByRole('button', { name: /open menu/i });

        // If the table is not wide enough to show
        await openMenu.scrollIntoViewIfNeeded();

        await openMenu.click();
        await this.page.getByRole('menuitem', { name: /Delete/i }).click();

        await this.page.getByRole('button', { name: /Delete/i }).click();
    }
}
