// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
