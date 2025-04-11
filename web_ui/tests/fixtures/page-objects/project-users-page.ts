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

export class ProjectUsersPage {
    constructor(private page: Page) {}

    async getUserRow(email: string) {
        return this.page.getByRole('row', { name: new RegExp(email) });
    }

    async addUser(email: string, role: string) {
        await this.page.getByRole('button', { name: 'add user to project' }).click();

        await expect(this.page.getByRole('dialog')).toBeVisible();

        await this.page.getByRole('combobox', { name: 'select user User' }).click();
        await this.page.getByRole('option', { name: new RegExp(email) }).click();
        await expect(this.page.getByRole('option', { name: new RegExp(email) })).toBeHidden();

        await this.page.getByRole('button', { name: 'Select a role Role' }).click();
        await this.page.getByRole('option', { name: role }).click();
        await expect(this.page.getByRole('option', { name: role })).toBeHidden();

        await this.page.getByRole('button', { name: 'Add' }).click();
        await expect(this.page.getByRole('dialog')).toBeHidden();
    }

    async removeUser(email: string) {
        const row = await this.getUserRow(email);
        await row.getByRole('button', { name: 'open menu' }).click();

        await expect(this.page.getByRole('menu')).toBeVisible();
        await this.page.getByRole('menuitem', { name: 'Delete' }).click();

        await expect(this.page.getByRole('alertdialog')).toBeVisible();
        await this.page.getByRole('button', { name: 'Delete' }).click();
    }

    async editUser(email: string, role: string) {
        const row = await this.getUserRow(email);
        await row.getByRole('button', { name: 'open menu' }).click();

        await expect(this.page.getByRole('menu')).toBeVisible();
        await this.page.getByRole('menuitem', { name: 'Edit' }).click();

        await expect(this.page.getByRole('dialog')).toBeVisible();
        await this.page.getByTestId('roles-add-user').click();
        await this.page.getByRole('option', { name: role }).click();
        await expect(this.page.getByRole('option', { name: role })).toBeHidden();
        await this.page.getByRole('button', { name: 'Save' }).click();
        await expect(this.page.getByRole('dialog')).toBeHidden();
    }

    async search(search: string | null) {
        if (search === null) {
            await this.page.getByRole('searchbox').clear();
        } else {
            await this.page.getByRole('searchbox').fill(search);
        }
    }
}
