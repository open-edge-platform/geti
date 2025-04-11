// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Page } from '@playwright/test';

import { ModelConfigurationOption } from '../../../src/pages/project-details/components/project-models/train-model-dialog/model-templates-selection/utils';

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
