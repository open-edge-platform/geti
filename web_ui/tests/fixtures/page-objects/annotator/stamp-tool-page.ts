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

import { Page } from '@playwright/test';

import { SelectionToolPage } from './selection-tool-page';

export class StampToolPage {
    constructor(
        private page: Page,
        private selectionTool: SelectionToolPage
    ) {}

    async selectSelectionTool() {
        await this.selectionTool.selectTool();
    }

    async cancelStampToolUsingButton() {
        await this.page.getByRole('button', { name: 'Cancel stamp' }).click();
    }

    async cancelStampToolUsingHotkey() {
        await this.page.keyboard.press('Escape');
    }

    async cancelStampToolUsingContextMenu(x: number, y: number) {
        await this.page.mouse.click(x, y, { button: 'right' });
        await this.page.getByRole('menuitem', { name: /Cancel stamp/ }).click();
    }

    async selectStampToolUsingButton() {
        await this.page.getByRole('button', { name: 'Create stamp' }).click();
    }

    async selectStampToolUsingHotkey() {
        await this.page.keyboard.press('s');
    }

    async selectStampToolUsingContextMenu(x: number, y: number) {
        await this.page.mouse.click(x, y, { button: 'right' });
        await this.page.getByRole('menuitem', { name: /Create stamp/ }).click();
    }
}
