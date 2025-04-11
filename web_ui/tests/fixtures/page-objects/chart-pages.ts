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

import fs from 'fs';

import { Locator, Page } from '@playwright/test';

import { expectToBeDownloaded } from '../../utils/expects';

const parseCSV = (data: string) => {
    return data
        .split('\n')
        .filter((row) => row.length > 0)
        .map((row) => row.split(',').map((cell) => cell.replace(/^"|"$/g, '')))
        .reduce((allRows, current) => {
            allRows.push(current);
            return allRows;
        }, [] as string[][]);
};

class ChartPage {
    constructor(
        private page: Page,
        private chartLocator: Locator
    ) {}

    private async openChartMenu() {
        await this.chartLocator.getByRole('button', { name: 'Download menu', exact: true }).click();
    }

    private getDownloadMenuOption(format: string) {
        return this.page.getByRole('menuitem', { name: format });
    }

    private async downloadChart(format: string) {
        await this.openChartMenu();
        await this.getDownloadMenuOption(format).click();
    }

    async downloadPDF() {
        await this.downloadChart('pdf');
    }

    async downloadCSV() {
        await this.downloadChart('csv');
    }

    async downloadAndReadCSV() {
        const downloadResolved = await expectToBeDownloaded(this.page, () => this.downloadCSV());

        const path = './downloads/' + downloadResolved.suggestedFilename();
        await downloadResolved.saveAs(path);

        const data = fs.readFileSync(path, 'utf8');

        return parseCSV(data);
    }

    async openFullScreen() {
        await this.chartLocator.getByRole('button', { name: /Open in fullscreen/ }).click();
    }

    async closeFullScreen() {
        await this.page.getByRole('button', { name: 'Close fullscreen' }).click();
    }
}

export class BarChartPage {
    private chartPage: ChartPage;
    private chartLocator: Locator;

    constructor(page: Page, chart: Locator) {
        this.chartPage = new ChartPage(page, chart);
        this.chartLocator = chart;
    }

    getColumn(metricName: string) {
        return this.chartLocator.getByLabel(metricName, { exact: true });
    }

    async downloadPDF() {
        await this.chartPage.downloadPDF();
    }

    async downloadAndReadCSV() {
        return this.chartPage.downloadAndReadCSV();
    }

    async openFullScreen() {
        await this.chartPage.openFullScreen();
    }

    async closeFullScreen() {
        await this.chartPage.closeFullScreen();
    }
}

export class LineChartPage {
    private chartPage: ChartPage;
    private chartLocator: Locator;

    constructor(page: Page, chart: Locator) {
        this.chartPage = new ChartPage(page, chart);
        this.chartLocator = chart;
    }

    async downloadPDF() {
        await this.chartPage.downloadPDF();
    }

    async downloadAndReadCSV() {
        return this.chartPage.downloadAndReadCSV();
    }

    async openFullScreen() {
        await this.chartPage.openFullScreen();
    }

    async closeFullScreen() {
        await this.chartPage.closeFullScreen();
    }

    getAxis(axisName: string) {
        return this.chartLocator.locator(`tspan`, { hasText: axisName });
    }

    getLine(axisName: string) {
        return this.chartLocator.getByLabel(`${axisName} line`, { exact: true });
    }
}

export class TextChartPage {
    private chartPage: ChartPage;
    private readonly chartLocator: Locator;

    constructor(page: Page, chart: Locator) {
        this.chartPage = new ChartPage(page, chart);
        this.chartLocator = chart;
    }

    async downloadPDF() {
        await this.chartPage.downloadPDF();
    }

    async downloadAndReadCSV() {
        return this.chartPage.downloadAndReadCSV();
    }

    getChart() {
        return this.chartLocator;
    }
}

export class RadialChartPage {
    private chartPage: ChartPage;
    private chartLocator: Locator;

    constructor(page: Page, chart: Locator) {
        this.chartPage = new ChartPage(page, chart);
        this.chartLocator = chart;
    }

    async downloadPDF() {
        await this.chartPage.downloadPDF();
    }

    async downloadAndReadCSV() {
        return this.chartPage.downloadAndReadCSV();
    }

    getMetric(metricName: string) {
        return this.chartLocator.getByLabel(metricName);
    }
}

export class ObjectSizeDistributionChartPage {
    private chartPage: ChartPage;
    private page: Page;
    private readonly chartLocator: Locator;

    constructor(page: Page, chart: Locator) {
        this.chartPage = new ChartPage(page, chart);
        this.chartLocator = chart;
        this.page = page;
    }

    async downloadPDF() {
        await this.chartPage.downloadPDF();
    }

    async downloadAndReadCSV() {
        return this.chartPage.downloadAndReadCSV();
    }

    async selectObjectClass(objectClass: string) {
        await this.chartLocator.getByRole('button', { name: /Object class/i }).click();
        await this.page.getByRole('option', { name: objectClass }).click();
    }

    getNumberOfObjects() {
        return this.chartLocator.getByLabel('Number of objects in Object size distribution');
    }
}
