// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Locator, Page } from '@playwright/test';

import { ViewModes } from './../../../src/shared/components/media-view-modes/utils';
import { FilterDialogPage } from './filter-dialog-page';

export class ProjectMediaBucketPage {
    constructor(
        private page: Page,
        private bucket: Locator
    ) {}

    async uploadFiles(files: string[], labels?: string[] | null) {
        // Extra guard check to make sure auto-waiting works
        await expect(this.bucket.getByRole('button', { name: /upload/i })).toBeVisible();

        await this.bucket.getByRole('button', { name: /upload/i }).click();

        const [fileChooser] = await Promise.all([
            // It is important to call waitForEvent before click to set up waiting.
            this.page.waitForEvent('filechooser'),
            this.page.getByRole('menuitem', { name: /files/i }).click(),
        ]);

        await fileChooser.setFiles(files);

        if (labels === null) {
            await this.page.getByRole('button', { name: /skip/i }).click();
        }

        if (labels) {
            for (const label of labels) {
                await this.page.getByRole('checkbox', { name: label }).check();
            }
            await this.page.getByRole('button', { name: /accept/i }).click();
        }
    }

    getBucketLocator(): Locator {
        return this.bucket;
    }

    async changeViewMode(name: ViewModes) {
        await this.page.getByRole('button', { name: /view mode/i }).click();
        await this.page.getByRole('menuitemradio', { name }).click();
    }

    async openFilterDialog() {
        await this.page
            .getByRole('button', {
                name: /filter media/i,
            })
            .click();

        const dialog = this.page.getByRole('dialog');
        await expect(dialog).toBeVisible();

        return new FilterDialogPage(this.page, dialog);
    }

    async selectImage(name: string) {
        const bucketLocator = this.getBucketLocator();
        const image = bucketLocator.getByRole('img', { name });

        await image.hover();
        await this.page.getByRole('checkbox', { name: /select media item/i }).click();
    }

    async deleteSelectedImages() {
        await this.bucket.getByRole('button', { name: /delete selected media/i }).click();

        const deletionDialog = this.page.getByRole('alertdialog');
        await expect(deletionDialog).toBeVisible();

        await this.page.getByRole('button', { name: 'Delete' }).click();
        await expect(deletionDialog).toBeHidden();
    }

    async openDetailsDialog() {
        const detailsDialog = this.page.getByRole('button', { name: 'Details' }).first();
        await detailsDialog.click();

        await expect(this.page.getByTestId('modal')).toBeVisible();
    }

    async cancelPendingUploads() {
        const cancelButton = this.page.getByRole('button', { name: 'Cancel all pending' });

        await expect(cancelButton).toBeVisible();

        await cancelButton.click();
    }

    async expectTotalMedia({ images = 0, videos = 0 }: { images?: number; videos?: number }) {
        if (images > 0) {
            await expect(this.bucket.getByTestId('count-message-id')).toContainText(
                `${images} image${images > 1 ? 's' : ''}`
            );
        }

        if (videos > 0) {
            await expect(this.bucket.getByTestId('count-message-id')).toContainText(
                `${videos} video${videos > 1 ? 's' : ''}`
            );
        }
    }
}
