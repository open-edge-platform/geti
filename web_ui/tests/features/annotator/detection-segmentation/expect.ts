// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

const getVisibleAnnotation = async (page: Page, labelId: string) => {
    const annotations = page.getByLabel('annotations', { exact: true });
    const predictionLabel = annotations.locator(`id=${labelId}-labels`).last();

    await expect(predictionLabel).toBeVisible();
    return predictionLabel;
};

export const expectAnnotationIsVisible = async (page: Page, labelId: string, labelName: string) => {
    const annotationLabel = await getVisibleAnnotation(page, labelId);
    await expect(annotationLabel.getByLabel(`annotation-${labelName}`)).toBeVisible();
};

export const expectSubmitToBeEnabled = async (page: Page) => {
    const submitButton = page.getByRole('button', { name: /submit annotations/i });

    await expect(submitButton).toBeEnabled();
};

export const expectToHaveAnnotationInputWithAnnotatedStatus = async (page: Page, annotationId: string) => {
    const wrapper = page.getByTestId(`annotation-${annotationId}-thumbnailWrapper`);
    const annotationStatus = wrapper.getByRole('button', { name: 'Annotated' });

    await expect(annotationStatus).toBeVisible();
};

export const expectNotToHaveAnnotationInputWithAnnotatedStatus = async (page: Page, annotationId: string) => {
    const wrapper = page.getByTestId(`annotation-${annotationId}-thumbnailWrapper`);
    const annotationStatus = wrapper.getByRole('button', { name: 'Annotated' });

    await expect(annotationStatus).toBeHidden();
};

export { expect };
