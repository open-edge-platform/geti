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
import { goToAnnotatorInActiveMode } from './utils';

test.describe('Check FUX notifications in Annotator', () => {
    // eslint-disable-next-line max-len
    test(`Check that Annotator Tools notification is shown by default when entering Annotator and clicking "Next" on it triggers Active Dataset notification (no matter if Annotator is in active mode or not)`, async ({
        page,
        registerApiResponse,
    }) => {
        registerStoreSettings(registerApiResponse, {
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                isEnabled: false,
            },
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: {
                isEnabled: true,
            },
        });
        await page.goto(
            // eslint-disable-next-line max-len
            `http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/62946c61003ddb3967f14750/datasets/6101254defba22ca453f11cc/annotator/image/613a23866674c43ae7a777aa?task-id=62946c61003ddb3967f1474f`
        );
        await expect(page.getByText('How to annotate my data?')).toBeVisible();
        await expect(page.getByText('What’s Active set?')).toBeHidden();

        await page.getByRole('button', { name: 'Next', exact: true }).click();

        await expect(page.getByText('What’s Active set?')).toBeVisible();
        await expect(page.getByText('How to annotate my data?')).toBeHidden();

        await page.getByTestId('selected-annotation-dataset-id').click();
        await page.getByRole('option', { name: 'Example chain project' }).click();

        await expect(page.getByText('What’s Active set?')).toBeVisible();
    });

    test('Check that clicking "Dismiss" dismisses only the targeted notification', async ({
        page,
        registerApiResponse,
    }) => {
        registerStoreSettings(registerApiResponse, {
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: {
                isEnabled: true,
            },
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: {
                isEnabled: true,
            },
        });

        await goToAnnotatorInActiveMode(page);

        await expect(page.getByText('How to annotate my data?')).toBeVisible();
        await expect(page.getByText('Continue annotating')).toBeVisible();

        registerStoreSettings(registerApiResponse, {
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                isEnabled: true,
            },
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: {
                isEnabled: false,
            },
        });
        // Note: Dismissing continue annotating notification
        await page.getByRole('button', { name: 'Dismiss help dialog', exact: true }).click();

        await expect(page.getByText('How to annotate my data?')).toBeVisible();
        await expect(page.getByText('Continue annotating')).toBeHidden();
    });

    test(`Check that reloading page doesn't change notification state`, async ({ page, registerApiResponse }) => {
        registerStoreSettings(registerApiResponse, {
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                isEnabled: false,
            },
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: {
                isEnabled: true,
            },
        });

        await goToAnnotatorInActiveMode(page);

        await expect(page.getByText('What’s Active set?')).toBeHidden();
        await expect(page.getByText('How to annotate my data?')).toBeVisible();

        await page.reload();

        await expect(page.getByText('What’s Active set?')).toBeHidden();
        await expect(page.getByText('How to annotate my data?')).toBeVisible();
    });

    test(`Check that next and back buttons are working properly`, async ({ page, registerApiResponse }) => {
        registerStoreSettings(registerApiResponse, {
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                isEnabled: true,
            },
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: {
                isEnabled: false,
            },
        });

        await goToAnnotatorInActiveMode(page);

        await expect(page.getByText('What’s Active set?')).toBeVisible();
        await expect(page.getByText('How to annotate my data?')).toBeHidden();

        await page.getByRole('button', { name: 'Back button' }).click();

        await expect(page.getByText('How to annotate my data?')).toBeVisible();
        await expect(page.getByText('What’s Active set?')).toBeHidden();

        await page.getByRole('button', { name: 'Next', exact: true }).click();

        await expect(page.getByText('What’s Active set?')).toBeVisible();
        await expect(page.getByText('How to annotate my data?')).toBeHidden();
    });

    test(`Check that user's first annotation triggers Continue Annotating Notification`, async ({
        page,
        registerApiResponse,
    }) => {
        registerStoreSettings(registerApiResponse, {
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: {
                isEnabled: false,
            },
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: {
                isEnabled: true,
            },
            [FUX_SETTINGS_KEYS.NEVER_ANNOTATED]: {
                value: false,
            },
        });

        await goToAnnotatorInActiveMode(page);

        await expect(page.getByText('Continue annotating')).toBeVisible();
    });
});
