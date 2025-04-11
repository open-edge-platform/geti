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

import { Locator, Page } from '@playwright/test';

import { DatasetTabActions } from '../../../src/pages/project-details/components/project-dataset/utils';
import { expect } from '../../fixtures/base-test';

export const expectDatasetMoreMenuToBeVisible = async (moreMenu: Locator) => {
    await expect(moreMenu).toBeVisible();
};

export const expectDatasetMoreMenuToBeInvisible = async (page: Page) => {
    await expect(page.getByRole('button', { name: /collapsed datasets/i })).toBeHidden();
};

const expectDatasetSelectionStatus = async (datasetTab: Locator, isSelected: 'true' | 'false') => {
    await expect(datasetTab).toHaveAttribute('aria-selected', isSelected);
};

export const expectDatasetTabToBeVisible = async (datasetTab: Locator) => {
    await expect(datasetTab).toBeVisible();
};

export const expectDatasetTabToBeInvisible = async (datasetTab: Locator) => {
    await expect(datasetTab).toBeHidden();
};

export const expectDatasetNotToBeSelected = async (datasetTab: Locator) => {
    await expectDatasetSelectionStatus(datasetTab, 'false');
};

export const expectDatasetToBeSelected = async (datasetTab: Locator) => {
    await expectDatasetSelectionStatus(datasetTab, 'true');
};

export const expectDatasetMenuItemToBeVisible = async (page: Page, datasetMenuItem: DatasetTabActions) => {
    await expect(page.getByRole('menuitem', { name: datasetMenuItem })).toBeVisible();
};

export const expectDatasetMenuItemToBeInvisible = async (page: Page, datasetMenuItem: DatasetTabActions) => {
    await expect(page.getByRole('menuitem', { name: datasetMenuItem })).toBeHidden();
};

export const expectURLToContainDatasetId = async (page: Page, datasetId: string) => {
    expect(page.url()).toContain(`datasets/${datasetId}`);
};

export const expectDatasetTabsCountToBe = async (page: Page, counter: number) => {
    const datasetTabs = page.getByRole('tablist', { name: /dataset page tabs/i }).getByRole('tab');

    await expect(datasetTabs).toHaveCount(counter);
};

export const expectDatasetTabsToBeLoaded = async (page: Page) => {
    await expect(page.getByRole('tablist', { name: /dataset page tabs/i })).toBeVisible();
};
