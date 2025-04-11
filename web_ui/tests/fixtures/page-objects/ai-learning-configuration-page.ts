// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Page } from '@playwright/test';

import { InferenceModel } from '../../../src/core/annotations/services/visual-prompt-service';

export class AILearningConfigurationPage {
    constructor(private page: Page) {}

    async open() {
        await this.page.getByRole('button', { name: /Active learning configuration/i }).click();
        await expect(this.page.getByRole('heading', { name: /active learning configuration/i })).toBeVisible();
    }

    async close() {
        await this.page.mouse.click(0, 0);
    }

    async toggleSuggestPredictions() {
        await this.page.getByRole('switch', { name: /suggest predictions/i }).click();
    }

    async toggleAutoTraining() {
        await this.autoTrainingSwitch().click();
    }

    autoTrainingSwitch() {
        return this.page.getByRole('switch', { name: /toggle auto training/i });
    }

    async selectAdaptiveAnnotationsThreshold() {
        await this.adaptiveRequiredAnnotationsRadio().click();
    }

    adaptiveRequiredAnnotationsRadio() {
        return this.page.getByRole('radio', { name: /adaptive/i });
    }

    taskPicker() {
        return this.page.getByRole('button', {
            name: /select a task to configure its training settings/i,
        });
    }

    startTrainingButton() {
        return this.page.getByRole('button', { name: 'Start training' });
    }

    async selectInferenceMode(inferenceModel: InferenceModel) {
        switch (inferenceModel) {
            case InferenceModel.ACTIVE_MODEL: {
                await this.page.getByRole('radio', { name: 'Active learning model' }).click();
                break;
            }
            case InferenceModel.VISUAL_PROMPT: {
                await this.page.getByRole('radio', { name: 'Prompt model' }).click();
                break;
            }
        }
    }
}
