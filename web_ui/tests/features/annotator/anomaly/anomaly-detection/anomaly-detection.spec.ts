// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { DOMAIN } from '../../../../../src/core/projects/core.interface';
import { checkCommonElements, checkDetectionTools, checkNumberOfTools } from '../../../../fixtures/annotator-test';
import { test } from '../../../../fixtures/base-test';
import { waitForLoadingToBeFinished } from '../../../../utils/assertions';
import { annotatorUrl, media, project } from './../../../../mocks/anomaly/anomaly-detection/mocks';

test.describe('Anomaly detection', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
    });

    test('annotator page elements', async ({ page }) => {
        await page.goto(annotatorUrl);

        await waitForLoadingToBeFinished(page);
        await expect(page.getByTestId('project-name-domain-id')).toHaveText(
            'Example Anomaly detection project@ Anomaly detection'
        );

        await checkNumberOfTools(page, 3);

        await checkDetectionTools(page);

        await checkCommonElements(page, DOMAIN.ANOMALY_DETECTION);
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
