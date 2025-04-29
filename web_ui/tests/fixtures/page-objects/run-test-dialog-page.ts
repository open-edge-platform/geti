// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

export interface TestConfiguration {
    testName?: string;
    task?: string;
    model?: string;
    version?: string;
    optimization?: string;
    metric?: string;
    dataset?: string;
}

export class RunTestDialogPage {
    constructor(private page: Page) {}

    async inputTestName(testName: string) {
        const inputField = this.page.getByRole('textbox', { name: /test name/i });

        await inputField.fill(testName);
    }

    private async selectTask(task: string) {
        await this.page.getByRole('button', { name: /task type/i }).click();
        await this.page.getByRole('option', { name: new RegExp(task, 'i') }).click();
    }

    private async selectModel(model: string) {
        await this.page.getByRole('button', { name: /model$/i }).click();
        await this.page.getByRole('option', { name: new RegExp(model, 'i') }).click();
    }

    private async selectVersion(version: string) {
        await this.page.getByRole('button', { name: /version/i }).click();
        await this.page.getByRole('option', { name: new RegExp(version, 'i') }).click();
    }

    private async selectOptimization(optimization: string) {
        await this.page.getByRole('button', { name: /optimization/i }).click();
        await this.page
            .getByRole('option', { name: new RegExp(optimization, 'i') })
            .first()
            .click();
    }

    private async selectEvaluationMetric(metric: string) {
        await this.page.getByRole('button', { name: /Evaluation metric/i }).click();
        await this.page.getByRole('option', { name: new RegExp(metric, 'i') }).click();
    }

    private async selectDataset(dataset: string) {
        await this.page.getByRole('button', { name: /dataset/i }).click();
        await this.page.getByRole('option', { name: new RegExp(dataset, 'i') }).click();
    }

    async configureTest(configuration: TestConfiguration) {
        if (configuration.task) {
            await this.selectTask(configuration.task);
        }

        if (configuration.model) {
            await this.selectModel(configuration.model);
        }

        if (configuration.version) {
            await this.selectVersion(configuration.version);
        }

        if (configuration.testName !== undefined) {
            await this.inputTestName(configuration.testName);
        }

        if (configuration.optimization) {
            await this.selectOptimization(configuration.optimization);
        }

        if (configuration.metric) {
            await this.selectEvaluationMetric(configuration.metric);
        }

        if (configuration.dataset) {
            await this.selectDataset(configuration.dataset);
        }
    }

    getRunTestButton() {
        return this.page.getByRole('button', { name: /run test/i });
    }

    async runTest() {
        await this.getRunTestButton().click();
    }

    async getAlertMessage(): Promise<string> {
        return (await this.page.getByRole('alert').textContent()) ?? '';
    }
}
