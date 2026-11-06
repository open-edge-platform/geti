// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, Page } from '@playwright/test';

type SourceTypeLabel = 'USB Camera' | 'IP Camera' | 'Video file';
type SourceMenuAction = 'Connect' | 'Disconnect' | 'Test connection' | 'Edit' | 'Remove';

const VIDEO_UPLOAD_TIMEOUT = 1000 * 60;

export class SourcesPage {
    constructor(private page: Page) {}

    private getSourceTab() {
        return this.page.getByRole('tab').filter({ hasText: 'Source' });
    }

    getAddSourceButton() {
        return this.page.getByRole('button', { name: 'Add new source' });
    }

    getSourceCard(name: string) {
        return this.page.getByTestId(`source-card-${name}`);
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

    getMenuItem(action: SourceMenuAction) {
        return this.page.getByRole('menuitem', { name: action, exact: true });
    }

    async openAddSourceForm(type: SourceTypeLabel) {
        await this.getSourceTab().click();
        await this.getAddSourceButton().click();
        await this.page.getByRole('button', { name: type, exact: true }).click();
    }

    async openSourceMenu(name: string) {
        await this.getSourceTab().click();
        await this.getSourceCard(name).getByRole('button', { name: 'source menu' }).click();
    }

    async selectSourceMenuAction(name: string, action: SourceMenuAction) {
        await this.openSourceMenu(name);
        await this.getMenuItem(action).click();
    }

    async deleteSource(name: string) {
        await this.getSourceTab().click();

        await expect(this.getSourceCard(name)).toBeVisible();

        await this.openSourceMenu(name);

        const disconnect = this.getMenuItem('Disconnect');

        await expect(disconnect).toBeVisible();

        await disconnect.click();
        await expect(this.getToast(`disconnected from "${name}"`)).toBeVisible();
        await this.openSourceMenu(name);

        await this.getMenuItem('Remove').click();
    }

    async selectCamera(name?: string) {
        await this.page.getByRole('button', { name: 'Camera list' }).click();

        const options = this.page.getByRole('option');
        await (name === undefined ? options.first() : options.filter({ hasText: name })).click();
    }

    getVideoFileInput() {
        return this.page.getByTestId('upload-video-file');
    }

    async addUsbCameraSource({ name }: { name: string }) {
        await this.openAddSourceForm('USB Camera');

        await this.getNameField().fill(name);
        await this.selectCamera();

        await this.getAddAndUseButton().click();
    }

    async addVideoFileSource({
        name,
        videoPath,
        loop = true,
    }: {
        name: string;
        videoPath: string;
        loop?: boolean;
    }): Promise<string> {
        await this.openAddSourceForm('Video file');

        await this.getNameField().fill(name);
        await this.getVideoFileInput().setInputFiles(videoPath);

        const loopSwitch = this.page.getByRole('switch', { name: 'loop video' });

        if ((await loopSwitch.isChecked()) !== loop) {
            await loopSwitch.click();
        }

        const uploadResponse = this.page.waitForResponse(
            (response) => response.url().includes('/api/sources/media') && response.request().method() === 'POST',
            { timeout: VIDEO_UPLOAD_TIMEOUT }
        );

        await this.getAddAndUseButton().click();

        const { video_path: uploadedVideoPath } = (await (await uploadResponse).json()) as { video_path: string };

        return uploadedVideoPath;
    }
}
