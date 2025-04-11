// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../src/core/user-settings/dtos/user-settings.interface';
import { expect, test } from '../../fixtures/base-test';
import { registerStoreSettings } from '../../utils/api';
import {
    getScheduledAutoTrainingCostJob,
    getScheduledAutoTrainingJob,
    getScheduledTrainingCostJob,
} from '../credit-system/mocks';
import { getMockedJob } from '../project-dataset/mocks';
import {
    autoTrainingCreditSystemModalRegex,
    autoTrainingCreditSystemNotificationRegex,
    autoTrainingNotificationRegex,
    detectionProjectAutoTrainingConfig,
    manualTrainingCreditSystemToastNotificationRegex,
} from './utils';

const MODELS_PAGE_URL =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/63283aedc80c9c686fd3b1e6/models';

test.describe('Check FUX notifications on models page', () => {
    test.describe('Check notification with enabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

        test.beforeEach(async ({ registerApiResponse }) => {
            registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
                res(ctx.json({ incoming: 10, available: 100 }))
            );
            registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                res(ctx.status(200), ctx.json(detectionProjectAutoTrainingConfig))
            );
        });

        // eslint-disable-next-line max-len
        test('On manually triggered training toast notification should be displayed, not the autotraining modal', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledTrainingCostJob([]))));
            await page.goto(MODELS_PAGE_URL);

            await expect(page.getByRole('heading', { name: autoTrainingCreditSystemModalRegex })).toBeHidden();
            await expect(page.getByText(manualTrainingCreditSystemToastNotificationRegex)).toBeVisible();
        });

        test('On scheduled auto-training modal should appear and notification after the modal was dismissed', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: true },
            });
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));
            await page.goto(MODELS_PAGE_URL);

            await expect(page.getByText(autoTrainingCreditSystemModalRegex)).toBeVisible();
            await page.getByRole('button', { name: /dismiss/i }).click();

            await expect(page.getByText(autoTrainingCreditSystemNotificationRegex)).toBeVisible();
        });
    });

    test.describe('Check notification with disabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: false } });

        test('Check that Tutorial Card is visible when no model training or trained', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) =>
                res(
                    ctx.status(200),
                    ctx.json({
                        jobs: [getMockedJob()],
                        jobs_count: {
                            n_scheduled_jobs: 0,
                            n_running_jobs: 1,
                            n_finished_jobs: 0,
                            n_failed_jobs: 0,
                            n_cancelled_jobs: 0,
                        },
                    })
                )
            );
            registerApiResponse('GetModelGroups', (_, res, ctx) => {
                return res(ctx.json({ model_groups: [] }));
            });

            await page.goto(MODELS_PAGE_URL);
            await expect(page.getByText('No Trained Models Detected')).toBeVisible();
        });

        test('Check that Tutorial Card is not displayed when model is already trained', async ({ page }) => {
            await page.goto(MODELS_PAGE_URL);
            await expect(page.getByText('No Trained Models Detected')).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test('No training notification should be displayed after triggering manual training with disabled FEATURE_FLAG_CREDIT_SYSTEM', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledTrainingCostJob([]))));
            await page.goto(MODELS_PAGE_URL);

            await expect(page.getByRole('heading', { name: autoTrainingCreditSystemModalRegex })).toBeHidden();
            await expect(page.getByText(manualTrainingCreditSystemToastNotificationRegex)).toBeHidden();
        });

        test('On scheduled auto-training "Auto-training Scheduled Notification" should appear', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));
            registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                res(ctx.status(200), ctx.json(detectionProjectAutoTrainingConfig))
            );
            registerStoreSettings(registerApiResponse, {
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: { value: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: true },
            });
            await page.goto(MODELS_PAGE_URL);

            await expect(page.getByText(autoTrainingNotificationRegex)).toBeVisible();
        });
    });
});
