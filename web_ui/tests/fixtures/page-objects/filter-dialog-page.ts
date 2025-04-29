// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Locator, Page } from '@playwright/test';

export class FilterDialogPage {
    constructor(
        private page: Page,
        private dialog: Locator
    ) {}

    async addNewFilter() {
        await this.page.getByRole('button', { name: /new filter/i }).click();
    }

    async setAnnotationStatusFilter(state: 'Unannotated' | 'Annotated' | 'Partially annotated' | 'Revisit') {
        const listitem = await this.getLastFilterRow();

        // Select field
        await listitem.getByRole('button', { name: /media\-filter\-field/ }).click();
        await this.page.getByRole('menuitemradio', { name: 'Annotation status' }).click();
        await expect(this.page.getByRole('menu')).toBeHidden();

        // Select operator
        await listitem.getByRole('button', { name: /media\-filter\-operator/ }).click();
        await this.page.getByRole('menuitemradio', { name: 'Equal' }).click();
        await expect(this.page.getByRole('menu')).toBeHidden();

        // Select annotation status state
        await listitem.getByRole('button', { name: /media\-filter\-annotation\-scene\-state/i }).click();
        await this.page.getByRole('menuitemradio', { name: state }).click();
        await expect(this.page.getByRole('menu')).toBeHidden();
    }

    async setMediaNameFilter(name: string) {
        const listitem = await this.getLastFilterRow();

        // Select field
        await listitem.getByRole('button', { name: /media\-filter\-field/ }).click();
        await this.page.getByRole('menuitemradio', { name: 'Media name' }).click();
        await expect(this.page.getByRole('menu')).toBeHidden();

        // Select operator
        await listitem.getByRole('button', { name: /media\-filter\-operator/ }).click();
        await this.page.getByRole('menuitemradio', { name: 'Equal', exact: true }).click();
        await expect(this.page.getByRole('menu')).toBeHidden();

        // Fill in search
        await listitem.getByRole('textbox').fill(name);
    }

    async close() {
        await this.page.keyboard.press('Escape');
        await expect(this.dialog).toBeHidden();
    }

    private async getLastFilterRow() {
        const list = this.page.getByRole('list');

        const listitems = list.getByRole('listitem');

        return listitems.nth((await listitems.count()) - 1);
    }
}
