// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
