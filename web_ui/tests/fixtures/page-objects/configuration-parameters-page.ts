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

import { idMatchingFormat } from '../../../src/test-utils/id-utils';

export class ConfigurationParametersPage {
    constructor(private page: Page) {}

    async openConfigurableParameters() {
        await this.page.getByRole('button', { name: 'Reconfigure active model' }).click();
    }

    async openTrainNewModelConfigurableParameters() {
        await this.page.getByRole('button', { name: 'Train model' }).click();
        await this.page.getByRole('radio', { name: 'MANUAL_CONFIGURATION' }).click();
        await this.page.getByRole('button', { name: 'Next' }).click();
    }

    async closeConfigurableParameters() {
        this.page.getByRole('button', { name: 'Close' });
    }

    async openParametersSection(task: string) {
        await this.page.getByTestId(`${idMatchingFormat(task)}-fold-unfold-button`).click();
    }

    async openParametersGroup(groupName: string) {
        await this.page.getByText(groupName).click();
    }

    async toggleTiling(isOn: boolean) {
        const tilingSwitch = this.page.getByRole('switch', { name: 'enable_tiling' });
        await tilingSwitch.click();
        isOn ? await expect(tilingSwitch).toBeChecked() : await expect(tilingSwitch).not.toBeChecked();
    }

    async checkTilingParametersVisibility(isVisible: boolean) {
        const parameters = [
            'Max object per tile',
            'Tile Overlap',
            'Sampling Ratio for entire tiling',
            'Tile Image Size',
        ];

        for (const parameter of parameters) {
            isVisible
                ? await expect(this.page.getByText(parameter)).toBeVisible()
                : await expect(this.page.getByText(parameter)).toBeHidden();
        }
    }
}
