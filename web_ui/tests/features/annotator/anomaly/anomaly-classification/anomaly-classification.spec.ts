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

import { expect } from '@playwright/test';

import { DOMAIN } from '../../../../../src/core/projects/core.interface';
import { checkCommonElements } from '../../../../fixtures/annotator-test';
import { test } from '../../../../fixtures/base-test';
import { waitForLoadingToBeFinished } from '../../../../utils/assertions';
import { annotatorUrl, media, project } from './../../../../mocks/anomaly/anomaly-classification/mocks';

test.use({ featureFlags: { FEATURE_FLAG_ANOMALY_REDUCTION: false } });

test.describe('Anomaly classification', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
    });

    test('Annotator page elements', async ({ page }) => {
        await page.goto(annotatorUrl);

        await waitForLoadingToBeFinished(page);
        await expect(page.getByTestId('project-name-domain-id')).toHaveText(
            'Example Anomaly classification project@ Anomaly classification'
        );

        await checkCommonElements(page, DOMAIN.ANOMALY_CLASSIFICATION);
    });

    test('It does not allow the user to select the active set', async ({ page }) => {
        await page.goto(`${annotatorUrl}?active=true`);

        await waitForLoadingToBeFinished(page);

        const button = page.getByRole('button', { name: /choose annotation dataset/i });
        await expect(button).toContainText('Dataset');

        await button.click();
        await expect(page.getByRole('option', { name: 'Active set' })).toBeHidden();
        await expect(page.getByRole('option', { name: 'Dataset' })).toBeVisible();
    });
});
