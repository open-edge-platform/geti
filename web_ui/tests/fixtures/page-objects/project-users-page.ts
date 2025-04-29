// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
