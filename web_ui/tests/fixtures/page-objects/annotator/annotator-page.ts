// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Page } from '@playwright/test';

export class AnnotatorPage {
    constructor(private page: Page) {}

    async selectAnnotationMode() {
        await this.page.getByRole('button', { name: 'Select annotation mode' }).click();
    }

    async selectPredictionMode() {
        await this.page.getByRole('button', { name: 'Select prediction mode' }).click();
    }

    async submit() {
        await this.page.getByLabel('Submit annotations').click();
    }

    async deleteAllAnnotations() {
        await this.page.getByTestId('annotations-list-select-all').click();
        await this.page.getByTestId('annotations-list-delete-selected').click();
    }

    async selectedMediaFilename() {
        const contentinfo = this.page.getByRole('contentinfo');
        const fileInfo = (await contentinfo.getByLabel('media name').textContent()) ?? '';
        return fileInfo.split(' (')[0];
    }

    async goBackToProjectPage() {
        await this.page.getByTestId('go-back-button').click();
    }
}
