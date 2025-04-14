// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Locator, Page } from '@playwright/test';

export class LabelShortcutsPage {
    constructor(private page: Page) {}

    async openLabelShortcutsMenu() {
        await this.page.getByRole('button', { name: /More/ }).click();
    }

    async closeLabelShortcutsMenu() {
        // Click outside of the menu to close it
        await this.page.mouse.click(0, 0);
    }

    async pinLabel(labelName: string) {
        const label = await this.locateLabel(labelName);

        await label.scrollIntoViewIfNeeded();
        await label.hover();
        await label.getByRole('button', { name: /pin/ }).click();
    }

    async unpinLabel(labelName: string) {
        const label = await this.locateLabel(labelName);

        await label.scrollIntoViewIfNeeded();
        await label.hover();
        await label.getByRole('button', { name: /unpin/ }).click();
    }

    async getPinnedLabelLocator(labelName: string, exact = true) {
        const labelShortcuts = await this.getPinnedLabelShortcutsLocator();

        return labelShortcuts.getByRole('button', { name: labelName, exact });
    }

    private async locateLabel(labelName: string): Promise<Locator> {
        const labelButtons = await this.page
            .getByRole('button', {
                name: /click to show child labels/i,
            })
            .all();

        for (let idx = 0; idx < labelButtons.length; idx++) {
            await labelButtons[0].click();
        }

        const label = this.page.getByRole('listitem', { name: `label item ${labelName}` });

        if (await label.isVisible()) {
            return label;
        }

        return this.locateLabel(labelName);
    }

    private async getPinnedLabelShortcutsLocator() {
        return this.page.getByRole('list', { name: 'Label shortcuts' });
    }
}
