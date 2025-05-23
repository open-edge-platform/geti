// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { ModelIdentifier } from '../../../src/core/models/models.interface';
import { paths } from '@geti/core/src/services/routes';
import { BarChartPage, LineChartPage, RadialChartPage, TextChartPage } from './chart-pages';

export class ModelMetricsPage {
    constructor(private page: Page) {}

    async openByURL(
        { organizationId, modelId, projectId, groupId, workspaceId }: ModelIdentifier = {
            organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
            modelId: '59e96bd31b6b242caaf77a1c',
            projectId: '59e94836734b717fbbfe0b75',
            groupId: '59e94836734b717fbbfe0b79',
            workspaceId: '61011e42d891c82e13ec92da',
        }
    ) {
        await this.page.goto(
            paths.project.models.model.statistics({
                organizationId,
                workspaceId,
                projectId,
                modelId,
                groupId,
            })
        );
    }

    getTrainingDate() {
        return this.page.getByTestId('training-date-id');
    }

    getModelTrainingTime() {
        return this.page.getByTestId('training-duration-id');
    }

    getJobDuration() {
        return this.page.getByTestId('training-job-duration-id');
    }

    getLoadingMetricsMessage() {
        return this.page.getByText('Preparing statistics... Please try again in a few minutes.');
    }

    getErrorMessage() {
        return this.page.getByText('An unexpected error occurred during statistics preparation.');
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

    getFullScreenLineChart(chartName: string): LineChartPage {
        return new LineChartPage(this.page, this.getFullScreenChart(chartName));
    }

    getRadialChart(chartName: string) {
        return new RadialChartPage(this.page, this.getChart(chartName));
    }

    getTextChart(chartName: string) {
        return new TextChartPage(this.page, this.getChart(chartName));
    }

    getLineChart(chartName: string) {
        return new LineChartPage(this.page, this.getChart(chartName));
    }

    async downloadAll() {
        await this.page.getByRole('button', { name: 'download svg' }).click();
    }
}
