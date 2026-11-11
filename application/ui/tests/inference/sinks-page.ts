// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, Page } from '@playwright/test';

type OutputFormatLabel = 'Predictions' | 'Image Original' | 'Image with Predictions';
type SinkTypeLabel = 'Folder' | 'Webhook' | 'MQTT';
type SinkMenuAction = 'Connect' | 'Disconnect' | 'Test connection' | 'Edit' | 'Remove';

export class SinksPage {
    constructor(private page: Page) {}

    private getSinkTab() {
        return this.page.getByRole('tab').filter({ hasText: 'Sink' });
    }

    private getAddSinkButton() {
        return this.page.getByRole('button', { name: 'Add new sink' });
    }

    getSinkCard(name: string) {
        return this.page.getByTestId(`sink-card-${name}`);
    }

    getNameField() {
        return this.page.getByRole('textbox', { name: 'Name', exact: true });
    }

    getToast(message: string | RegExp) {
        return this.page.getByLabel('toast').filter({ hasText: message });
    }

    getAddAndUseButton() {
        return this.page.getByRole('button', { name: 'Add & Use' });
    }

    getSaveButton() {
        return this.page.getByRole('button', { name: 'Save', exact: true });
    }

    getSaveAndConnectButton() {
        return this.page.getByRole('button', { name: 'Save & Connect' });
    }

    getMenuItem(action: SinkMenuAction) {
        return this.page.getByRole('menuitem', { name: action, exact: true });
    }

    async openAddSinkForm(type: SinkTypeLabel) {
        await this.getSinkTab().click();
        await this.getAddSinkButton().click();
        await this.page.getByRole('button', { name: type, exact: true }).click();
    }

    async openSinkMenu(name: string) {
        await this.getSinkTab().click();
        await this.getSinkCard(name).getByRole('button', { name: 'sink menu' }).click();
    }

    async selectSinkMenuAction(name: string, action: SinkMenuAction) {
        await this.openSinkMenu(name);
        await this.getMenuItem(action).click();
    }

    async deleteSink(name: string) {
        await this.getSinkTab().click();

        await expect(this.getSinkCard(name)).toBeVisible();

        await this.openSinkMenu(name);

        const disconnect = this.getMenuItem('Disconnect');

        await expect(disconnect).toBeVisible();
        await disconnect.click();
        await expect(this.getToast(`disconnected from "${name}"`)).toBeVisible();

        await this.openSinkMenu(name);
        await this.getMenuItem('Remove').click();
    }

    async selectOutputFormats(outputFormats: OutputFormatLabel[]) {
        for (const outputFormat of outputFormats) {
            await this.page.getByRole('checkbox', { name: outputFormat, exact: true }).check();
        }
    }

    async fillRateLimit(samples: number, seconds: number) {
        await this.page.getByRole('textbox', { name: 'Samples' }).fill(String(samples));
        await this.page.getByRole('textbox', { name: 'Seconds' }).fill(String(seconds));
    }

    async addFolderSink({
        name,
        folderPath,
        outputFormats,
        rateLimitSamples = 1,
        rateLimitSeconds = 1,
    }: {
        name: string;
        folderPath: string;
        outputFormats: OutputFormatLabel[];
        rateLimitSamples?: number;
        rateLimitSeconds?: number;
    }) {
        await this.openAddSinkForm('Folder');

        await this.getNameField().fill(name);
        await this.page.getByRole('textbox', { name: 'Folder Path' }).fill(folderPath);
        await this.fillRateLimit(rateLimitSamples, rateLimitSeconds);
        await this.selectOutputFormats(outputFormats);

        await this.getAddAndUseButton().click();
    }
}
