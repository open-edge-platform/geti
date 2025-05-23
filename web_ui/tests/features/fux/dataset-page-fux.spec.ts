// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';

import {
    FUX_NOTIFICATION_KEYS,
    FUX_SETTINGS_KEYS,
    TUTORIAL_CARD_KEYS,
} from '../../../src/core/user-settings/dtos/user-settings.interface';
import { expect, test } from '../../fixtures/base-test';
import { project } from '../../mocks/anomaly/anomaly-classification/mocks';
import { registerStoreSettings } from '../../utils/api';
import { getScheduledAutoTrainingJob, projectConfigAutoTrainingOnMock } from '../credit-system/mocks';
import { autoTrainingNotificationRegex, goToAnnotatorInActiveMode } from './utils';

const PROJECT_DATASET_URL = paths.project.dataset.media({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: '61011e42d891c82e13ec92da',
    projectId: '62946c61003ddb3967f14750',
    datasetId: '6101254defba22ca453f11cc',
});

test.describe('Check FUX notifications on dataset page', () => {
    test.beforeEach(async ({ registerApiResponse }) => {
        registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
            res(ctx.status(200), ctx.json(projectConfigAutoTrainingOnMock))
        );
    });

    test.describe('Check notification with enabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

        test('Check that clicking "Reset help dialogs" also resets credit system notifications', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: true,
                },
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: {
                    isEnabled: true,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: project.id,
                },
            });
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));

            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('The auto-training job has been started')).toBeVisible();
            await expect(page.getByRole('heading', { name: 'Building a good dataset' })).toBeVisible();

            // The first click closes the "The auto-training job has ..." notification that is popover
            await page.getByLabel('close first user experience notification').click();

            await expect(page.getByText('The auto-training job has been started')).toBeHidden();

            await page.getByLabel('Documentation actions').click();
            await page.getByText('Reset help dialogs').click();

            // After resetting, FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION turns to "false"
            await expect(page.getByText('The auto-training job has been started')).toBeHidden();
        });

        test('Check that clicking "Dismiss all" dismisses all help dialogs', async ({ page, registerApiResponse }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: true,
                },
                [TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL]: {
                    isEnabled: true,
                },
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: {
                    isEnabled: false,
                },
            });
            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeVisible();
            await expect(page.getByText('Building a good dataset')).toBeVisible();
            await expect(page.getByText('The auto-training job has been started')).toBeHidden();

            await page.getByTestId('projectDatasetTutorial-more-btn-id').click();
            await page.getByText('Dismiss all').click();

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeHidden();
            await expect(page.getByText('Building a good dataset')).toBeHidden();
            await expect(page.getByText('The auto-training job has been started')).toBeHidden();
        });
    });

    test.describe('Check notification with disabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: false } });

        // eslint-disable-next-line max-len
        test('Check that for Non-anomalous project with media items in dataset both tutorial card and Start Annotating notification are visible', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: true,
                },
            });
            await page.goto(PROJECT_DATASET_URL);
            await expect(page.getByText('Click here to start annotating your dataset.')).toBeVisible();
            await expect(page.getByText('Building a good dataset')).toBeVisible();
        });

        // eslint-disable-next-line max-len
        test('Check that clicking "close" closes targeted notification only and notifications state doesnt change after reload', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: true,
                },
            });
            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeVisible();
            await expect(page.getByText('Building a good dataset')).toBeVisible();

            await page.getByLabel('Dismiss help dialog').click();

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeHidden();
            await expect(page.getByText('Building a good dataset')).toBeVisible();

            await page.reload();

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeHidden();
            await expect(page.getByText('Building a good dataset')).toBeVisible();
        });

        // eslint-disable-next-line max-len
        test('Check that for empty dataset tutorial card is visible but Start Annotating Notification is not visible', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('FilterMedia', async (_request, res, ctx) => {
                return res(
                    ctx.json({
                        media: [],
                        total_matched_images: 0,
                        total_matched_videos: 0,
                        total_matched_video_frames: 0,
                        total_images: 0,
                        total_videos: 0,
                    }),
                    ctx.status(200)
                );
            });

            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('Building a good dataset')).toBeVisible();
            await expect(page.getByText('Start annotating your dataset using interactive learning.')).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test('Check that for Anomalous project with media items in dataset tutorial card is visible but Start Annotating Notification is not visible', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));

            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('Building a good dataset')).toBeVisible();
            await expect(page.getByText('Start annotating your dataset using interactive learning.')).toBeHidden();
        });

        test('Check that navigating to annotator resets "Start annotating" notification', async ({
            registerApiResponse,
            page,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: true,
                },
            });
            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeVisible();

            await page.getByRole('button', { name: 'Annotate interactively' }).click();
            await page.goto(PROJECT_DATASET_URL);

            // wait for the sidebar with links to be visible
            await expect(page.getByRole('link', { name: /datasets/i })).toBeVisible();
            await expect(page.getByText('Click here to start annotating your dataset.')).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test('When a job is scheduled with auto-training ON, "Auto-training Scheduled Notification" should appear', async ({
            registerApiResponse,
            page,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
                    isEnabled: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: {
                    value: false,
                },
            });
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));
            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText(autoTrainingNotificationRegex)).toBeVisible();
        });

        test('Check that clicking "Dismiss all" dismisses all help dialogs', async ({ page, registerApiResponse }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: true,
                },
                [TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL]: {
                    isEnabled: true,
                },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
                    isEnabled: false,
                },
            });
            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeVisible();
            await expect(page.getByText('Building a good dataset')).toBeVisible();
            await expect(page.getByText(autoTrainingNotificationRegex)).toBeHidden();

            await page.getByLabel('Open to dismiss all help dialogs').click();
            await page.getByText('Dismiss all').click();

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeHidden();
            await expect(page.getByText('Building a good dataset')).toBeHidden();
            await expect(page.getByText(autoTrainingNotificationRegex)).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test('Check that clicking "Dismiss all" on tutorial card dismisses all help dialogs including notifications, "Reset help dialogs" brings back initial state of FUX notifications', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: true,
                },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                    isEnabled: true,
                },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: {
                    isEnabled: true,
                },
            });
            await page.goto(PROJECT_DATASET_URL);

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeVisible();
            await expect(page.getByText('Building a good dataset')).toBeVisible();

            await page.getByRole('button', { name: 'Open to dismiss all help dialogs' }).click();
            await page.getByRole('menuitem', { name: 'Dismiss all' }).click();

            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText('Active dataset')).toBeHidden();
            await expect(page.getByText('Continue annotating')).toBeHidden();

            await page.goto(PROJECT_DATASET_URL);

            // wait for the sidebar with links to be visible
            await expect(page.getByRole('link', { name: /datasets/i })).toBeVisible();
            await expect(page.getByText('Click here to start annotating your dataset.')).toBeHidden();
            await expect(page.getByText('Building a good dataset')).toBeHidden();

            await page.getByLabel('Documentation actions').click();
            await page.getByText('Reset help dialogs').click();

            await expect(page.getByText('Click here to start annotating your dataset.')).toBeVisible();
            await expect(page.getByText('Building a good dataset')).toBeVisible();
        });
    });
});
