// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Locator, Page } from '@playwright/test';

import { TestConfiguration } from '../../fixtures/page-objects/run-test-dialog-page';

export const expectTestConfiguration = async (page: Page, configuration: TestConfiguration) => {
    const dialog = page.getByRole('dialog');

    if (configuration.testName !== undefined) {
        await expect(dialog.getByRole('textbox', { name: /test name/i })).toHaveValue(configuration.testName);
    }

    if (configuration.task) {
        await expect(dialog).toContainText(configuration.task, { ignoreCase: true });
    }

    if (configuration.model) {
        await expect(dialog).toContainText(configuration.model, { ignoreCase: true });
    }

    if (configuration.version) {
        await expect(dialog).toContainText(configuration.version, { ignoreCase: true });
    }

    if (configuration.optimization) {
        await expect(dialog).toContainText(configuration.optimization, { ignoreCase: true });
    }

    if (configuration.metric) {
        await expect(dialog).toContainText(configuration.metric, { ignoreCase: true });
    }

    if (configuration.dataset) {
        await expect(dialog).toContainText(configuration.dataset, { ignoreCase: true });
    }
};

export const getGlobalAnnotation = async (page: Page | Locator): Promise<Locator> => {
    const globalAnnotation = page.getByLabel('annotations', { exact: true }).getByLabel('labels');

    await expect(globalAnnotation).toHaveCount(1);
    await expect(globalAnnotation).toBeVisible();

    return globalAnnotation;
};

export const expectAGlobalAnnotationToExist = async (page: Page | Locator) => {
    await expect(await getGlobalAnnotation(page)).toBeVisible();
};

export const expectAnnotationToHaveLabels = async (
    annotation: Locator,
    labels: { name: string; probability?: number }[]
) => {
    await expect(annotation).toBeVisible();

    if (labels.length === 0) {
        return expect(annotation).toContainText('Select label');
    }

    return Promise.all(
        labels.map((label) => {
            return expect(annotation).toContainText(label.name);
        })
    );
};

export const expectAnnotationNotToHaveLabels = (
    annotation: Locator,
    labels: { name: string; probability?: number }[]
) => {
    if (labels.length === 0) {
        return expect(annotation).not.toContainText('Select label');
    }

    return Promise.all(
        labels.map((label) => {
            return expect(annotation).not.toContainText(label.name);
        })
    );
};

export const expectToBeOnTheTestPage = async (page: Page) => {
    await expect(
        page.getByRole('navigation', { name: 'Breadcrumbs' }).getByRole('link', { name: 'Tests' })
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: /annotations vs predictions/i })).toBeVisible();
};
