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
