// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { test } from '../../fixtures/base-test';
import { BarChartPage, LineChartPage } from '../../fixtures/page-objects/chart-pages';
import { expectToBeDownloaded } from '../../utils/expects';
import { modelDetailsResponse, modelGroupResponse, modelMetricsResponse } from './mocks';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const barChartExample = modelMetricsResponse.model_statistics.find((chart) => chart.type === 'bar')!;
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const lineChartExample = modelMetricsResponse.model_statistics.find((chart) => chart.type === 'line')!;

type BarChartType = typeof barChartExample;
type LineChartType = typeof lineChartExample;

const expectBarChartToBeVisible = async ({ barChart, chart }: { chart: BarChartType; barChart: BarChartPage }) => {
    for (const metric of chart.value) {
        const bar = barChart.getColumn(metric.header);

        await expect(bar).toBeVisible();
        await expect(bar).toHaveAttribute('aria-valuenow', metric.value.toString());
    }
};

const expectLineChartToBeVisible = async ({ chart, lineChart }: { chart: LineChartType; lineChart: LineChartPage }) => {
    await expect(lineChart.getAxis(chart.value.x_axis_label)).toBeVisible();
    await expect(lineChart.getAxis(chart.value.y_axis_label)).toBeVisible();

    for (const lineData of chart.value.line_data) {
        const line = lineChart.getLine(lineData.header);

        await expect(line).toBeVisible();
        await expect(line).toHaveAttribute(
            'aria-valuetext',
            lineData.points.map(({ x, y }) => `x: ${x}, y: ${y}`).join(', ')
        );
    }
};

test.describe('Model metrics', () => {
    const metricsWithoutTrainingTime = modelMetricsResponse.model_statistics.filter(
        (chart) => !['Training date', 'Training job duration', 'Training duration'].includes(chart.header)
    );

    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetModelDetail', (_, res, ctx) => {
            return res(ctx.json(modelDetailsResponse));
        });

        registerApiResponse('GetModelGroup', (_, res, ctx) => {
            return res(ctx.json(modelGroupResponse));
        });
    });

    test('Displays and downloads model metrics', async ({ modelMetricsPage, registerApiResponse, page }) => {
        registerApiResponse('GetModelStatistics', (_, res, ctx) => {
            return res(ctx.json(modelMetricsResponse));
        });

        await modelMetricsPage.openByURL();

        await expect(modelMetricsPage.getTrainingDate()).toContainText('25 February 2025');
        await expect(modelMetricsPage.getTrainingDate()).toContainText('10:39:22 AM');
        await expect(modelMetricsPage.getModelTrainingTime()).toContainText('00:04:26');
        await expect(modelMetricsPage.getJobDuration()).toContainText('00:08:22');

        for (const chart of metricsWithoutTrainingTime) {
            if (chart.type === 'bar') {
                const barChart = modelMetricsPage.getBarChart(chart.header);

                await expectBarChartToBeVisible({
                    barChart,
                    chart,
                });

                await barChart.openFullScreen();

                const barChartInFullScreen = modelMetricsPage.getFullScreenBarChart(chart.header);

                await expectBarChartToBeVisible({
                    barChart: barChartInFullScreen,
                    chart,
                });
                await expectToBeDownloaded(page, () => barChartInFullScreen.downloadPDF());

                await barChartInFullScreen.closeFullScreen();
            } else if (chart.type === 'radial_bar') {
                const radialChart = modelMetricsPage.getRadialChart(chart.header);
                const radialChartMetric = radialChart.getMetric(chart.value[0].header);

                await expect(radialChartMetric).toBeVisible();
                await expect(radialChartMetric).toHaveAttribute(
                    'aria-valuenow',
                    (chart.value[0].value * 100).toString()
                );

                await expectToBeDownloaded(page, () => radialChart.downloadPDF());
            } else if (chart.type === 'text') {
                const textChart = modelMetricsPage.getTextChart(chart.header);

                await expect(textChart.getChart()).toBeVisible();
                await expect(textChart.getChart()).toContainText(chart.value.toString());

                await expectToBeDownloaded(page, () => textChart.downloadPDF());
            } else if (chart.type === 'line') {
                const lineChart = modelMetricsPage.getLineChart(chart.header);
                await expectLineChartToBeVisible({ lineChart, chart });

                await lineChart.openFullScreen();

                const lineChartInFullScreen = modelMetricsPage.getFullScreenLineChart(chart.header);

                await expectLineChartToBeVisible({ lineChart: lineChartInFullScreen, chart });
                await expectToBeDownloaded(page, () => lineChartInFullScreen.downloadPDF());

                await lineChartInFullScreen.closeFullScreen();
            }
        }

        await expectToBeDownloaded(page, () => modelMetricsPage.downloadAll());
    });

    test('Downloads CSV with model metrics', async ({ modelMetricsPage, registerApiResponse }) => {
        registerApiResponse('GetModelStatistics', (_, res, ctx) => {
            return res(ctx.json(modelMetricsResponse));
        });

        await modelMetricsPage.openByURL();

        await expect(modelMetricsPage.getTrainingDate()).toContainText('25 February 2025');

        for (const chart of metricsWithoutTrainingTime) {
            if (chart.type === 'bar') {
                const barChart = modelMetricsPage.getBarChart(chart.header);
                const csvContent = await barChart.downloadAndReadCSV();

                expect(csvContent).toEqual(
                    chart.value.reduce(
                        (acc, curr) => {
                            acc[0].push(curr.header);
                            acc[1].push(curr.value.toString());
                            return acc;
                        },
                        [[], []] as string[][]
                    )
                );
            } else if (chart.type === 'line') {
                const lineChart = modelMetricsPage.getLineChart(chart.header);
                const csvContent = await lineChart.downloadAndReadCSV();

                expect(csvContent).toEqual(
                    chart.value.line_data.reduce(
                        (acc, curr) => {
                            curr.points.forEach((point) => {
                                acc.push([point.x.toString(), point.y.toString()]);
                            });

                            return acc;
                        },
                        [[chart.value.x_axis_label, chart.value.y_axis_label]] as string[][]
                    )
                );
            } else if (chart.type === 'radial_bar') {
                const radialBarChart = modelMetricsPage.getRadialChart(chart.header);
                const csvContent = await radialBarChart.downloadAndReadCSV();

                expect(csvContent).toEqual([[chart.value[0].header], [`${(chart.value[0].value * 100).toString()}`]]);
            } else if (chart.type === 'text') {
                const textChart = modelMetricsPage.getTextChart(chart.header);
                const csvContent = await textChart.downloadAndReadCSV();

                expect(csvContent).toEqual([[chart.header], [chart.value.toString()]]);
            }
        }
    });

    test('Displays "Preparing statistics" when they are not available yet', async ({
        modelMetricsPage,
        registerApiResponse,
    }) => {
        registerApiResponse('GetModelStatistics', (_, res, ctx) => {
            return res(ctx.status(404));
        });

        await modelMetricsPage.openByURL();

        await expect(modelMetricsPage.getLoadingMetricsMessage()).toBeVisible();
    });

    test('Displays an error message when an unexpected error occurs', async ({
        modelMetricsPage,
        registerApiResponse,
    }) => {
        registerApiResponse('GetModelStatistics', (_, res, ctx) => {
            return res(
                ctx.json({
                    model_statistics: [],
                })
            );
        });

        await modelMetricsPage.openByURL();

        await expect(modelMetricsPage.getErrorMessage()).toBeVisible();
    });
});
