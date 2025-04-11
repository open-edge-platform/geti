// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Page } from '@playwright/test';

export class IntelAdminPage {
    constructor(private page: Page) {}

    async goToOrganizationsListPage() {
        await this.page.goto('/intel-admin/organizations');
    }

    async filterByNameOrEmail(nameOrEmail: string) {
        const searchField = this.page.getByLabel(/Search by name or email/);

        await searchField.fill(nameOrEmail);
    }

    async filterByOrganizationStatus(status: string) {
        const dropdownField = this.page.getByRole('button', { name: /Organizations status/ });

        await dropdownField.click();
        await this.page.getByRole('option', { name: status }).click();
    }

    async clearSearchField() {
        await this.page.getByRole('button', { name: /Clear search/ }).click();
    }

    async clickSendInvite() {
        await this.page.getByRole('button', { name: /Send invite/ }).click();
    }

    async fillInviteForm(email: string, orgName: string) {
        await expect(this.page.getByLabel(/Email address/)).toBeVisible();

        await this.page.getByLabel(/Email address/).fill(email);
        await this.page.getByLabel(/Organization name/).fill(orgName);

        await expect(this.page.getByRole('button', { name: /Send invite/ })).toBeEnabled();

        await this.clickSendInvite();
    }

    async selectRowMenu(name: string) {
        await this.page.getByRole('row', { name }).getByRole('button').click();
    }

    async deleteOrganization(name: string) {
        await this.selectRowMenu(name);
        await this.page.getByRole('menuitem', { name: 'Delete' }).click();
        await this.page.getByRole('button', { name: 'Delete' }).click();
    }

    async suspendOrganization(name: string) {
        await this.selectRowMenu(name);
        await this.page.getByRole('menuitem', { name: 'Suspend' }).click();
    }

    async activateOrganization(name: string) {
        await this.selectRowMenu(name);
        await this.page.getByRole('menuitem', { name: 'Activate' }).click();
    }
}
