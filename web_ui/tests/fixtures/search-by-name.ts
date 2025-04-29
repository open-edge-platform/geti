// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
