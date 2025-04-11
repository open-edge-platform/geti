// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
