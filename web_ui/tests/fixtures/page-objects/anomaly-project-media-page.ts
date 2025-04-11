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

import { Page } from '@playwright/test';

import { MEDIA_CONTENT_BUCKET } from '../../../src/providers/media-upload-provider/media-upload.interface';
import { ProjectMediaPage } from './project-media-page';

export class AnomalyProjectMediaPage {
    constructor(
        private page: Page,
        private projectMediaPage: ProjectMediaPage
    ) {}

    async getNormalBucket() {
        return this.projectMediaPage.getBucket(MEDIA_CONTENT_BUCKET.NORMAL);
    }

    async getAnomalousBucket() {
        return this.projectMediaPage.getBucket(MEDIA_CONTENT_BUCKET.ANOMALOUS);
    }

    async startTrainingFromNotification() {
        await this.page.getByRole('button', { name: /train/i }).click();

        // For SaaS, where we use the credit system, the button to start training includes the
        // amount of credits that will be consumed by the training
        const startTraining = this.page
            .getByRole('button', { name: /start/i })
            .or(this.page.getByRole('button', { name: /credits to consume/i }));

        await startTraining.click();
    }
}
