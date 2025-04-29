// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

export class UndoRedoPage {
    constructor(private page: Page) {}

    async undoUsingButton() {
        await this.page.getByRole('button', { name: 'undo' }).click();
    }

    async redoUsingButton() {
        await this.page.getByRole('button', { name: 'redo' }).click();
    }

    async undoUsingShortcut() {
        await this.page.keyboard.press('Control+Z');
    }

    async redoUsingShortcut() {
        await this.page.keyboard.press('Control+Y');
    }
}
