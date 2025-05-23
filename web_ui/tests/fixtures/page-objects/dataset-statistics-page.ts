// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { DatasetIdentifier } from '../../../src/core/projects/dataset.interface';
import { paths } from '@geti/core/src/services/routes';
import { BarChartPage, ObjectSizeDistributionChartPage } from './chart-pages';

export class DatasetStatisticsPage {
    constructor(private page: Page) {}

    getPage() {
        return this.page;
    }

    async openByURL(
        { organizationId, projectId, workspaceId, datasetId }: DatasetIdentifier = {
            organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
            projectId: '4dc8f244b7bfafc65898ed27',
            workspaceId: '61011e42d891c82e13ec92da',
            datasetId: '4dc8f244b7bfafc65898ed33',
        }
    ) {
        await this.page.goto(paths.project.dataset.statistics({ organizationId, workspaceId, projectId, datasetId }));
    }

    async selectTask(taskName: string) {
        await this.page.getByRole('button', { name: /Select task/ }).click();
        await this.page.getByRole('option', { name: taskName }).click();
    }

    getImagesCount() {
        return this.page.getByTestId('media-images-count-id');
    }

    getVideosCount() {
        return this.page.getByTestId('media-videos-count-id');
    }

    getAnnotatedImagesCount() {
        return this.page.getByTestId('annotated-images-count-id');
    }

    getAnnotatedImagesProgressbar() {
        return this.page.getByLabel('Annotated images');
    }

    getAnnotatedVideosCount() {
        return this.page.getByTestId('annotated-videos-count-id');
    }

    getAnnotatedFramesCount() {
        return this.page.getByTestId('annotated-frame-count-id');
    }

    private getFullScreenChart(chartName: string) {
        return this.page.getByRole('dialog', { name: `${chartName} fullscreen` });
    }

    private getChart(chartName: string) {
        return this.page.getByLabel(`${chartName} chart`, { exact: true });
    }

    getBarChart(chartName: string): BarChartPage {
        return new BarChartPage(this.page, this.getChart(chartName));
    }

    getFullScreenBarChart(chartName: string): BarChartPage {
        return new BarChartPage(this.page, this.getFullScreenChart(chartName));
    }

    getObjectSizeDistributionChart() {
        return new ObjectSizeDistributionChartPage(this.page, this.getChart('Object size distribution'));
    }

    async downloadAll() {
        await this.page.getByRole('button', { name: 'download svg' }).click();
    }
}
