// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Page } from '@playwright/test';

export class CameraPage {
    constructor(private page: Page) {}

    async openCameraPage() {
        await this.page.getByRole('button', { name: /upload media/i }).click();
        await this.page.getByLabel('camera').click();
    }

    async openCameraPageAnomaly(bucket: string) {
        await this.page
            .getByTestId(`${bucket}-content-id`)
            .getByRole('button', { name: /upload media/i })
            .click();
        await this.page.getByLabel('camera').click();
    }

    async canTakePhotos() {
        await expect(this.page.getByRole('button', { name: 'photo capture' })).toBeEnabled();

        if (await this.page.getByLabel('close notification', { exact: true }).isVisible()) {
            await this.page.getByLabel('close notification', { exact: true }).click();
        }
    }

    async takeSinglePhoto() {
        await this.page.getByRole('button', { name: 'photo capture' }).click();
    }

    async viewAllCaptures() {
        await this.page.getByRole('link', { name: 'view all captures' }).click();
    }

    async acceptPhotos() {
        await this.page.getByRole('button', { name: 'Accept' }).click();
    }

    async discardAllPhotos() {
        // Trigger the confirmation dialog
        await this.page.getByRole('button', { name: 'Discard all' }).click();

        // Confirm
        await this.page.getByRole('button', { name: 'Discard all' }).click();
    }

    async closeCameraPage() {
        await this.page.getByRole('button', { name: 'Cancel' }).click();
    }

    async deletePhoto() {
        const thumbnail = this.page.getByLabel(new RegExp(/media item \w+/));

        // Hover and click on the "trash" icon
        await thumbnail.hover();
        await this.page.getByRole('button', { name: 'delete' }).click();

        // Confirm deletion by pressing the "delete" button on the dialog
        await this.page.getByRole('button', { name: 'delete' }).click();
    }
}
