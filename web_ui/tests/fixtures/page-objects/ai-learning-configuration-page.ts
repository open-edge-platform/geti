// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
