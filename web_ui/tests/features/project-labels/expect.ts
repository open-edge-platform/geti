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

import { expect, Page } from '@playwright/test';

import { idMatchingFormat } from '../../../src/test-utils/id-utils';

export const expectLabelToExist = async (page: Page, labelName: string, group?: boolean) => {
    const testId = group ? `${labelName}-project-label-group-input-id` : `label-tree-${labelName}-name-input`;

    const label = page.getByTestId(testId);

    await expect(label).toBeVisible();
};

export const expectElementToExistDisplayMode = async (page: Page, labelName: string) => {
    const label = page.getByLabel(`label item ${labelName}`);

    await expect(label).toBeVisible();
};

export const expectLabelToHaveBadge = async (page: Page, labelName: string, badge: string) => {
    const badgeLocator = page.locator(`#label-state-${badge}-${idMatchingFormat(labelName)}`);

    await expect(badgeLocator).toBeVisible();
};

export const expectLabelToHaveShortcut = async (page: Page, labelName: string, hotkey: string) => {
    const shortcut = page.getByLabel(`${labelName} label`).getByLabel('edited hotkey');
    await expect(shortcut).toHaveValue(hotkey);
};

export const expectLabelToHaveConflict = async (page: Page, labelName: string) => {
    await expect(page.getByTestId('label-error-message-id')).toHaveText(`Label '${labelName}' already exists`);
};
