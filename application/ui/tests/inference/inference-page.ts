// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Page } from '@playwright/test';

import { paths } from '../../src/constants/paths';

export class InferencePage {
    constructor(private page: Page) {}

    async goto(projectId: string = 'id-1') {
        await this.page.goto(paths.project.inference({ projectId }));
    }

    getToast(message: string | RegExp) {
        return this.page.getByLabel('toast').filter({ hasText: message });
    }

    async openInferenceTab() {
        await this.page.getByRole('tab', { name: 'Inference' }).click();
    }

    private getPipelineConfigurationTab() {
        return this.page.getByRole('button', { name: 'Toggle Pipeline configuration tab' });
    }

    async openPipelineConfiguration() {
        const tab = this.getPipelineConfigurationTab();

        if ((await tab.getAttribute('aria-pressed')) !== 'true') {
            await tab.click();
        }
    }

    getSourceTab() {
        return this.page.getByRole('tab').filter({ hasText: 'Source' });
    }

    getSinkTab() {
        return this.page.getByRole('tab').filter({ hasText: 'Sink' });
    }

    // Targets the trigger button, not the visually hidden native select that shares the label.
    getModelPicker() {
        return this.page.getByRole('button', { name: /active model/i });
    }

    async selectModel(name: string) {
        await this.getModelPicker().click();
        await this.page.getByRole('option', { name }).click();
    }

    getPipelineSwitch(state: 'enabled' | 'disabled') {
        return this.page.getByRole('switch', { name: `Pipeline ${state}` });
    }

    getPipelineHealth() {
        return this.page.getByRole('status');
    }

    async enablePipeline() {
        await this.getPipelineSwitch('disabled').click();
    }

    async disablePipeline() {
        await this.getPipelineSwitch('enabled').click();
    }
}
