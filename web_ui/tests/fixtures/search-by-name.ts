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

const FILTER_FIELD_ID = 'media-filter-field';
const FILTER_OPERATOR_ID = 'media-filter-operator';
const FILTER_NAME_ID = 'media-filter-name';

export const openAndTypeIntoSearchField = async (page: Page, value: string, id = '') => {
    await page.getByTestId(`${id}search-media-button-id`).click();

    const mediaSearchInput = page.getByTestId(`${id}search-field-media-id`);
    await mediaSearchInput.fill(value);
};

export const triggerFilterModal = async (page: Page, id = '') => {
    await page.getByTestId(`${id}filter-media-button`).click();
};

export const acceptFilter = async (page: Page, id = '') => {
    const mediaSearchInput = page.getByTestId(`${id}search-field-media-id`);

    await mediaSearchInput.click();
    await mediaSearchInput.press('Enter');
};

const checkFilterValue = async (page: Page, key: string, value: string) => {
    if (key === FILTER_NAME_ID) {
        await expect(page.getByRole('textbox', { name: key })).toHaveValue(value);
    } else {
        await expect(page.getByRole('button', { name: key })).toHaveText(value);
    }
};

export const checkChipsValue = async (page: Page, value: string, id = '') => {
    await expect(page.getByTestId(`${id}chip-search-rule-id`)).toHaveText(value);
};

export const checkMediaNameFilter = async (page: Page, value: string) => {
    await checkFilterValue(page, FILTER_FIELD_ID, 'Media name');
    await checkFilterValue(page, FILTER_OPERATOR_ID, 'Contains');
    await checkFilterValue(page, FILTER_NAME_ID, value);
};

export const closeSearchByNameFilterPopover = async (page: Page, id = '') => {
    await page.getByTestId(`${id}search-media-button-id`).focus();
};

export const checkSearchByNameFilterChip = async (page: Page, value: string, id = '') => {
    await openAndTypeIntoSearchField(page, value);

    await closeSearchByNameFilterPopover(page);

    await expect(page.getByTestId(`${id}chip-search-rule-id`)).toHaveText(`Media name contains ${value}`);
};
