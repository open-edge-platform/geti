// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
