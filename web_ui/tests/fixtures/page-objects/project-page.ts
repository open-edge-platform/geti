// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Locator, Page } from '@playwright/test';

import { LabelsPage } from './labels-page';
import { ProjectModelsPage } from './models-page';
import { ProjectTestsPage } from './tests-page';

export class ProjectPage {
    constructor(private page: Page) {}

    async goToLabelsPage() {
        const labelsLink = this.page.getByRole('link', { name: /labels/i });

        await labelsLink.click();

        return new LabelsPage(this.page);
    }

    async goToDatasetPage() {
        const datasetLink = this.page.getByRole('link', { name: /datasets/i });

        await datasetLink.click();

        return new LabelsPage(this.page);
    }

    async goToTestsPage() {
        const testsLink = this.page.getByRole('link', { name: /tests/i });

        await testsLink.click();

        return new ProjectTestsPage(this.page);
    }

    async goToModelsPage() {
        const modelsLink = this.page.getByRole('link', { name: /models/i });

        await modelsLink.click();

        return new ProjectModelsPage(this.page);
    }

    async getProjectType(): Promise<string | null> {
        return await this.page.getByLabel('Project type').textContent();
    }

    label(name: string): Locator {
        return this.page.getByRole('main').getByLabel(`${name} label`);
    }
}
