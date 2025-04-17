// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { ModelConfigurationOption } from '../../../src/pages/project-details/components/project-models/legacy-train-model-dialog/model-templates-selection/utils';

export class TrainModelDialogPage {
    constructor(private page: Page) {}

    async selectModelTemplate(modelTemplate: string) {
        await this.page.getByRole('radio', { name: modelTemplate }).check();
    }

    async selectModelConfigurationOption(option: ModelConfigurationOption) {
        await this.page.getByRole('radio', { name: option }).check();
    }

    async selectModelAlgorithm(name: string) {
        await this.page.getByRole('radio', { name }).check();
    }

    async nextStep() {
        await this.page.getByRole('button', { name: /Next/i }).click();
    }

    async previousStep() {
        await this.page.getByRole('button', { name: /Back/i }).click();
    }

    async train() {
        // For SaaS, where we use the credit system, the button to start training includes the
        // amount of credits that will be consumed by the training
        const trainButton = this.page
            .getByRole('button', { name: /start/i })
            .or(this.page.getByRole('button', { name: /credits to consume/i }));

        await trainButton.click();
    }

    async selectTaskType(taskType: string) {
        await this.page.getByRole('button', { name: /select domain task/i }).click();

        await this.page.getByRole('option', { name: new RegExp(taskType, 'i'), exact: false }).click();
    }
}
