// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
