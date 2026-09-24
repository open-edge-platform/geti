// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Locator, Page } from '@playwright/test';

type OutputFormatLabel = 'Predictions' | 'Image Original' | 'Image with Predictions';

const VIDEO_UPLOAD_TIMEOUT = 1000 * 60;

export class InferencePage {
    constructor(private page: Page) {}

    async openInferenceTab() {
        await this.page.getByRole('tab', { name: 'Inference' }).click();
    }

    private getPipelineConfigurationTab() {
        return this.page.getByRole('button', { name: 'Toggle Pipeline configuration tab' });
    }

    async openPipelineConfiguration() {
        const tab = this.getPipelineConfigurationTab();

        if ((await tab.getAttribute('aria-pressed')) !== 'true') {
            await tab.click();
        }
    }

    getInputTab() {
        return this.page.getByRole('tab').filter({ hasText: 'Input' });
    }

    getOutputTab() {
        return this.page.getByRole('tab').filter({ hasText: 'Output' });
    }

    getAddSourceButton() {
        return this.page.getByRole('button', { name: 'Add new source' });
    }

    private getAddSinkButton() {
        return this.page.getByRole('button', { name: 'Add new sink' });
    }

    getSourceCard(name: string) {
        return this.page.getByTestId(`source-card-${name}`);
    }

    async deleteSource(name: string) {
        await this.getInputTab().click();

        await this.removeCard(this.getSourceCard(name), 'source menu', name);
    }

    getSinkCard(name: string) {
        return this.page.getByTestId(`sink-card-${name}`);
    }

    async deleteSink(name: string) {
        await this.getOutputTab().click();

        await this.removeCard(this.getSinkCard(name), 'sink menu', name);
    }

    /**
     * Removes a source or sink card, disconnecting it from the pipeline first because the menu keeps
     * "Remove" disabled while it is connected.
     *
     * Missing cards are ignored so this can run as teardown after a test that failed before creating them.
     */
    private async removeCard(card: Locator, menuLabel: string, name: string) {
        if (!(await card.isVisible())) {
            return;
        }

        const menuButton = card.getByRole('button', { name: menuLabel });

        await menuButton.click();

        const disconnect = this.page.getByRole('menuitem', { name: 'Disconnect' });

        if (await disconnect.isVisible()) {
            await disconnect.click();

            await this.page
                .getByLabel('toast')
                .filter({ hasText: `disconnected from "${name}"` })
                .waitFor();

            await menuButton.click();
        }

        await this.page.getByRole('menuitem', { name: 'Remove' }).click();
    }

    /** Adds a USB camera source, picking the first camera the backend reports. */
    async addUsbCameraSource({ name }: { name: string }) {
        await this.getInputTab().click();
        await this.getAddSourceButton().click();
        await this.page.getByRole('button', { name: 'USB Camera', exact: true }).click();

        await this.page.getByRole('textbox', { name: 'Name', exact: true }).fill(name);
        await this.page.getByRole('button', { name: 'Camera list' }).click();
        await this.page.getByRole('option').first().click();

        await this.page.getByRole('button', { name: 'Add & Use' }).click();
    }

    /**
     * Adds a video file source by uploading the video to the backend, returning the path the backend
     * stored it at.
     *
     * The "Upload" button opens a native file picker, but it delegates to a hidden `<input type="file">`
     * that Playwright can set directly. Uploading rather than typing a path keeps the test independent of
     * where the backend runs: the bytes travel over HTTP and the backend stores them on its own filesystem.
     */
    async addVideoFileSource({
        name,
        videoPath,
        loop = true,
    }: {
        name: string;
        videoPath: string;
        loop?: boolean;
    }): Promise<string> {
        await this.getInputTab().click();
        await this.getAddSourceButton().click();

        await this.page.getByRole('button', { name: 'Video file', exact: true }).click();

        await this.page.getByRole('textbox', { name: 'Name', exact: true }).fill(name);
        await this.page.getByTestId('upload-video-file').setInputFiles(videoPath);

        const loopSwitch = this.page.getByRole('switch', { name: 'loop video' });

        if ((await loopSwitch.isChecked()) !== loop) {
            await loopSwitch.click();
        }

        const uploadResponse = this.page.waitForResponse(
            (response) => response.url().includes('/api/sources/media') && response.request().method() === 'POST',
            { timeout: VIDEO_UPLOAD_TIMEOUT }
        );

        await this.page.getByRole('button', { name: 'Add & Use' }).click();

        const { video_path: uploadedVideoPath } = (await (await uploadResponse).json()) as { video_path: string };

        return uploadedVideoPath;
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
        await this.getOutputTab().click();
        await this.getAddSinkButton().click();

        await this.page.getByRole('button', { name: 'Folder', exact: true }).click();

        await this.page.getByRole('textbox', { name: 'Name', exact: true }).fill(name);
        await this.page.getByRole('textbox', { name: 'Folder Path' }).fill(folderPath);

        await this.page.getByRole('textbox', { name: 'Samples' }).fill(String(rateLimitSamples));
        await this.page.getByRole('textbox', { name: 'Seconds' }).fill(String(rateLimitSeconds));

        for (const outputFormat of outputFormats) {
            await this.page.getByRole('checkbox', { name: outputFormat, exact: true }).check();
        }

        await this.page.getByRole('button', { name: 'Add & Use' }).click();
    }

    // Targets the trigger button, not the visually hidden native select that shares the label.
    getModelPicker() {
        return this.page.getByRole('button', { name: /active model/i });
    }

    async selectModel(name: string) {
        await this.getModelPicker().click();
        await this.page.getByRole('option', { name }).click();
    }

    getPipelineSwitch(state: 'enabled' | 'disabled') {
        return this.page.getByRole('switch', { name: `Pipeline ${state}` });
    }

    getPipelineHealth() {
        return this.page.getByRole('status');
    }

    async enablePipeline() {
        await this.getPipelineSwitch('disabled').click();
    }

    async disablePipeline() {
        await this.getPipelineSwitch('enabled').click();
    }
}
