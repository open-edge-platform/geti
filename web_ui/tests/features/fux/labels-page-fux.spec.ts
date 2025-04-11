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

import { expect } from '@playwright/test';

import { paths } from '../../../src/core/services/routes';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../src/core/user-settings/dtos/user-settings.interface';
import { test } from '../../fixtures/base-test';
import { registerStoreSettings } from '../../utils/api';
import {
    getScheduledAutoTrainingCostJob,
    getScheduledAutoTrainingJob,
    getScheduledTrainingJob,
    projectConfigAutoTrainingOnMock,
} from '../credit-system/mocks';
import {
    autoTrainingCreditSystemModalRegex,
    autoTrainingCreditSystemNotificationRegex,
    autoTrainingNotificationRegex,
    manualTrainingCreditSystemToastNotificationRegex,
} from './utils';

const projectIdentifier = {
    workspaceId: '6101a',
    projectId: '6101b',
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
};
const LABELS_PAGE_URL = paths.project.labels(projectIdentifier);

test.describe('FUX Notifications on labels page', () => {
    test.describe('Check notification with disabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: false } });

        // eslint-disable-next-line max-len
        test('When a job is scheduled with auto-training ON, "Auto-training Scheduled Notification" should appear', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));
            registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                res(ctx.status(200), ctx.json(projectConfigAutoTrainingOnMock))
            );
            registerStoreSettings(registerApiResponse, {
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: { value: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: true },
            });

            await page.goto(LABELS_PAGE_URL);

            await expect(page.getByText(autoTrainingNotificationRegex)).toBeVisible();
        });
    });

    test.describe('Check notification with enabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

        // eslint-disable-next-line max-len
        test('On scheduled auto-training "Credit System Modal" should appear and "Credit System Notification" should appear after the modal was dismissed', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: true },
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: { isEnabled: false },
            });
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));
            registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                res(ctx.status(200), ctx.json(projectConfigAutoTrainingOnMock))
            );

            await page.goto(LABELS_PAGE_URL);

            await expect(page.getByText(autoTrainingCreditSystemModalRegex)).toBeVisible();
            await page.getByRole('button', { name: /dismiss/i }).click();

            await expect(page.getByText(autoTrainingCreditSystemModalRegex)).toBeHidden();
            await expect(page.getByText(autoTrainingCreditSystemNotificationRegex)).toBeVisible();
        });

        test('On manually triggered training toast notification should be displayed', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledTrainingJob())));
            await page.goto(LABELS_PAGE_URL);

            await expect(page.getByText(manualTrainingCreditSystemToastNotificationRegex)).toBeVisible();
        });
    });
});
