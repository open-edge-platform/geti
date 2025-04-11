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

import { expect, Locator, Page } from '@playwright/test';

export class PersonalAccessTokenPage {
    constructor(private page: Page) {}

    async fromWorkspaces() {
        await this.page.getByRole('link', { name: 'Account' }).click();
        await this.page.getByRole('tab', { name: /token/i }).click();
    }

    async createToken() {
        await this.page.getByRole('button', { name: 'Create' }).click();

        const dialog = this.page.getByRole('dialog', { name: 'api-key-dialog' });
        await expect(dialog).toBeVisible();

        return new CreatePersonalAccessTokenDialogPage(this.page);
    }
}

class CreatePersonalAccessTokenDialogPage {
    public name: Locator;
    public description: Locator;
    public cancelButton: Locator;
    public createButton: Locator;

    constructor(private page: Page) {
        this.name = this.page.getByRole('textbox', { name: /name/i });
        this.description = this.page.getByRole('textbox', { name: /description/i });
        this.cancelButton = this.page.getByRole('button', { name: /Cancel/i });
        this.createButton = this.page.getByRole('button', { name: /Create/i });
    }

    async setName(name: string) {
        await this.name.fill(name);
    }

    async setDescription(description: string) {
        await this.description.fill(description);
    }

    async setExpirationDate(date: Date) {
        const day = date.toLocaleDateString('en-En', { day: 'numeric' });
        const year = date.toLocaleDateString('en-En', { year: 'numeric' });
        const month = date.toLocaleDateString('en-En', { month: 'numeric' });

        await this.page.getByRole('spinbutton', { name: /day, expiration date/i }).fill(day);
        await this.page.getByRole('spinbutton', { name: /month, expiration date/i }).fill(month);
        await this.page.getByRole('spinbutton', { name: /year, expiration date/i }).fill(year);
    }

    async fillExpirationDate(date: Date) {
        await this.page.getByRole('button', { name: 'Calendar Expiration date ​' }).click();

        //Note: Date.now were used to be able to select the date and check if proper value was put in the input
        //We have to know which date to select and it shouldn't be before today (not available in the component)
        //There are no operations on the date - it's save to use it
        //In the future we can think of mocking Date.now globally in the tests
        const today = date.toLocaleDateString('en-En', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });

        const [weekday, rest, year] = today.split(',');
        const [month, day] = rest.trim().split(' ');
        const currentYear = year.trim();

        await expect(
            this.page.getByTestId('popover').getByRole('heading', { name: `${month} ${currentYear}` })
        ).toBeVisible();

        const dateButton = this.page.getByRole('button', {
            name: `Today, ${weekday}, ${month} ${day}, ${currentYear}, First available date`,
        });
        await dateButton.click();
    }

    async create(): Promise<string> {
        const context = this.page.context();
        await context.grantPermissions(['clipboard-read', 'clipboard-write']);

        await this.createButton.click();

        // Copy token and get it form clipboard
        await this.page.getByRole('button', { name: /Copy/i }).click();
        const handle = await this.page.evaluateHandle(() => navigator.clipboard.readText());
        const clipboardContent = await handle.jsonValue();

        return clipboardContent;
    }
}
