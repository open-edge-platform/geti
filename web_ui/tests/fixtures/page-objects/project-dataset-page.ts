// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Locator, Page } from '@playwright/test';

import { DatasetTabActions } from '../../../src/pages/project-details/components/project-dataset/utils';
import { ImportProjectDatasetPage } from './import-project-dataset.page';

export class ProjectDatasetPage {
    constructor(private page: Page) {}

    async getCreateDatasetButton(): Promise<Locator> {
        return this.page.getByRole('button', { name: /create dataset/i });
    }

    async getDatasetMoreMenu(): Promise<Locator> {
        return this.page.getByRole('button', { name: /collapsed datasets/i });
    }

    async goToDatasetURL(projectId: string, datasetId: string) {
        await this.page.goto(
            // eslint-disable-next-line max-len
            `organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/${projectId}/datasets/${datasetId}`
        );
    }

    async getDatasetTab(datasetName: string): Promise<Locator> {
        return this.page.locator(`[role="tab"]:has(span:text("${datasetName}"))`);
    }

    async getDatasetTabMenu(datasetName: string): Promise<Locator> {
        return (await this.getDatasetTab(datasetName)).getByRole('button', { name: /open dataset menu/i });
    }

    async selectDatasetTab(datasetName: string) {
        await (await this.getDatasetTab(datasetName)).click();
    }

    async openDatasetTabMenu(datasetName: string) {
        await (await this.getDatasetTabMenu(datasetName)).click();
    }

    async selectDatasetTabMenuItem(datasetName: string, menuItem: DatasetTabActions) {
        await this.openDatasetTabMenu(datasetName);
        await this.page.getByRole('menuitem', { name: menuItem }).click();

        return new ImportProjectDatasetPage(this.page);
    }

    async createDataset() {
        await (await this.getCreateDatasetButton()).click();
    }

    getMediaTab() {
        return this.page.getByRole('tab', { name: /media/i });
    }

    getStatisticsTab() {
        return this.page.getByRole('tab', { name: /statistics/i });
    }
}
