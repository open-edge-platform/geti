// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Locator, Page } from '@playwright/test';

import { changeSlider } from '../../../utils/mouse';
import { expect } from '../../base-test';

export class VideoPlayerPage {
    constructor(private page: Page) {}

    async getTotalFrames(): Promise<number> {
        const text = this.page.getByLabel('Total frames number');
        const totalFrames = Number((await text.textContent()) ?? 0) + 1;

        return totalFrames;
    }

    async next() {
        await this.page.getByRole('button', { name: /go to next frame/i }).click();
    }

    async previous() {
        await this.page.getByRole('button', { name: /go to previous frame/i }).click();
    }

    async nextFrameUsingKeyboardShortcut() {
        await this.page.keyboard.press('ArrowRight');
    }

    async previousFrameUsingKeyboardShortcut() {
        await this.page.keyboard.press('ArrowLeft');
    }

    async pause() {
        await this.page.getByRole('button', { name: /pause video/i }).click();
    }

    getPlayButton() {
        return this.page.getByRole('button', { name: /play video/i });
    }

    getMuteButton() {
        return this.page.getByRole('button', { name: /Mute video/i });
    }

    getUnMuteButton() {
        return this.page.getByRole('button', { name: /Unmute video/i });
    }

    async play() {
        await this.getPlayButton().click();
    }

    async goToFrame(frameNumber: number) {
        const totalFrames = await this.getTotalFrames();

        const sliderThumb = this.page.getByRole('slider', { name: 'Videoframe' });
        const slider = this.page.getByRole('group', { name: 'Videoframe' });

        const sliderBoundingBox = await slider.boundingBox();
        expect(sliderBoundingBox).not.toBeNull();

        await changeSlider(this.page, sliderThumb, slider, (frameNumber + 1) / totalFrames);
    }

    async getPropagateAnnotationsButton() {
        return this.page.getByRole('button', {
            name: /propagate annotations from current frame to next frame/i,
        });
    }

    async propagateAnnotations() {
        await (await this.getPropagateAnnotationsButton()).click();
    }

    async enableActiveFrames() {
        await this.page.getByRole('switch', { name: /active frames/i }).check();
    }

    async disableActiveFrames() {
        await this.page.getByRole('switch', { name: /active frames/i }).uncheck();
    }

    async getCurrentFrameNumber(): Promise<number> {
        const currentlySelectedFrame = await this.page.getByLabel('Currently selected frame number').textContent();
        const matchFrameNumber = (currentlySelectedFrame ?? '').match(/current frame (\d+)/);
        const frameNumber = Number(matchFrameNumber?.at(1));

        return frameNumber;
    }

    async expectFrameNumberToBeSelected(frameNumber: number) {
        const text = this.page.getByLabel('Currently selected frame number');
        await expect(text).toContainText(`${frameNumber}`);
    }

    async openVideoTimeline() {
        await this.page.getByRole('button', { name: /open video annotator/i }).click();

        return this.timeline();
    }

    async closeVideoTimeline() {
        await this.page.getByRole('button', { name: /close video annotator/i }).click();
    }

    timeline() {
        return new VideoPlayerTimeline(this.page);
    }
}

class VideoPlayerTimeline {
    private grid: Locator;

    constructor(private page: Page) {
        this.grid = page.getByRole('grid');
    }

    async close() {
        await this.page.getByRole('button', { name: /close video annotator/i }).click();
    }

    async toggleFrameMode(): Promise<void> {
        await this.page.getByRole('button', { name: 'Toggle frame mode' }).click();
    }

    async expectFrameMode(mode: string): Promise<void> {
        await expect(this.page.getByTestId('frame-mode-indicator-id')).toHaveText(mode);
    }

    async expectUserLabel(frameNumber: number, labelName: string, childLabel = labelName) {
        const cell = await this.getCell(frameNumber, labelName);

        await expect(cell).toBeVisible();

        await expect(cell.getByLabel(childLabel, { exact: true })).toBeVisible();
    }

    async expectPredictedLabel(frameNumber: number, labelName: string) {
        const cell = await this.getCell(frameNumber, labelName);

        await expect(cell.getByLabel(`Predicted ${labelName}`, { exact: true })).toBeVisible();
    }

    async expectNoPredictedLabel(frameNumber: number, labelName: string) {
        const cell = await this.getCell(frameNumber, labelName);

        await expect(cell.getByLabel(`No prediction`, { exact: true })).toBeVisible();
    }

    async expectRowCount(rows: number) {
        await expect(this.grid).toHaveAttribute('aria-rowcount', rows.toString());
    }

    async expectColCount(cols: number) {
        await expect(this.grid).toHaveAttribute('aria-colcount', cols.toString());
    }

    private async getCell(frameNumber: number, labelName: string) {
        return this.grid.getByRole('gridcell', {
            name: `Label ${labelName} in frame number ${frameNumber}`,
            exact: true,
        });
    }
}
