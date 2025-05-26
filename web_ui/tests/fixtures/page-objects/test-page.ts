// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

export class ProjectTestPage {
    constructor(private page: Page) {}

    // Assumes text satisfies "/(\d)+ images, (\d)+ frames from (\d)+ videos/" and returns
    // the number before "images", for now we do not support testing videos (frames)
    private getImagesCount(text: string | null) {
        if (text === null) {
            return 0;
        }

        const matchImages = text.match(/(\d+) images/);

        if (matchImages) {
            return Number(matchImages[1]);
        }

        return 0;
    }

    async selectLabel(label: string) {
        await this.page.getByRole('button', { name: /select label/i }).click();
        await this.page.getByRole('option', { name: label }).click();
    }

    async countImages() {
        const info = this.page.getByText(/(\d)+ images, (\d)+ frames from (\d)+ videos/i);
        const imagesInBucketBelowThreshold = this.getImagesCount(await info.nth(0).textContent());
        const imagesInBucketAboveThreshold = this.getImagesCount(await info.nth(1).textContent());

        return imagesInBucketBelowThreshold + imagesInBucketAboveThreshold;
    }

    async getScore(): Promise<number> {
        const modelScore = this.page.getByLabel(/test model score/i);
        await expect(modelScore).toBeVisible();

        return parseFloat((await modelScore.getAttribute('aria-valuenow')) ?? '0');
    }

    async openMediaPreview(name: string) {
        const main = this.page.getByRole('main');
        await main.getByRole('img', { name }).click();
    }

    async closeMediaPreview() {
        await this.page.getByRole('button', { name: /close/i }).click();
    }

    async selectAnnotationMode() {
        await this.page.getByRole('button', { name: /select annotation mode/i }).click();
    }

    async selectPredictionMode() {
        await this.page.getByRole('button', { name: /select annotation mode/i }).click();
    }

    async sortBucketDescending() {
        await this.page.getByTestId(/below_threshold-sort-icon/).click();
    }

    async selectItemInPreview(name: string) {
        await this.page.getByRole('img', { name }).click();
    }

    async selectNextItemInPreview() {
        await this.page.getByRole('button', { name: 'next preview navigation' }).click();
    }
}
