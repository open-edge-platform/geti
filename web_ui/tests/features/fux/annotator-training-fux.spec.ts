// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../src/core/user-settings/dtos/user-settings.interface';
import {
    getMockedProjectStatusDTO,
    getMockedProjectStatusTask,
} from '../../../src/test-utils/mocked-items-factory/mocked-project';
import { expect, test } from '../../fixtures/base-test';
import { registerStoreSettings } from '../../utils/api';
import {
    getFinishedAutoTrainingJob,
    getFinishedTrainingJob,
    getScheduledAutoTrainingCostJob,
    getScheduledAutoTrainingJob,
    getScheduledTrainingCostJob,
    getScheduledTrainingJob,
    projectConfigAutoTrainingOffMock,
    projectConfigAutoTrainingOnMock,
} from '../credit-system/mocks';
import { project } from '../project-dataset/mocks';
import { getModelGroups } from '../project-models/models.mocks';
import {
    autoTrainingCreditSystemModalRegex,
    autoTrainingCreditSystemNotificationRegex,
    autoTrainingCreditSystemToastNotificationRegex,
    autoTrainingNotificationRegex,
    autoTrainingToastNotificationRegex,
    goToAnnotatorInActiveMode,
    manualTrainingCreditSystemToastNotificationRegex,
    startTaskTraining,
} from './utils';

test.describe('Check FUX notifications in Annotator related to training', () => {
    test.describe('Check notification with disabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: false } });

        test.beforeEach(({ registerApiResponse }) => {
            registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                res(ctx.status(200), ctx.json(projectConfigAutoTrainingOnMock))
            );
        });

        // eslint-disable-next-line max-len
        test('With a scheduled auto-training job, "Auto-training Scheduled Notification" should appear and "Continue Annotating" notification should not be shown', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: {
                    isEnabled: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_ANNOTATED]: {
                    value: false,
                },
            });

            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText('Continue annotating')).toBeVisible();

            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));

            await expect(page.getByText('Continue annotating')).toBeHidden();
            await expect(page.getByText(autoTrainingNotificationRegex)).toBeVisible();
        });

        // eslint-disable-next-line max-len
        test('With a scheduled auto-training job, "Credit System Modal" and "Credit System Notification" should not be shown', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: { value: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: true },
            });
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));

            await expect(page.getByText(autoTrainingCreditSystemModalRegex)).toBeHidden();
            await expect(page.getByText(autoTrainingCreditSystemNotificationRegex)).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test(`Check that first successfully finished auto-training will not trigger "Successfully Trained Notification" if FIRST_AUTOTRAINED_MODEL_ID doesn't match the id from job`, async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: { isEnabled: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
                    isEnabled: false,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: '60db493ed20945a0046f56ce',
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: {
                    value: 'job-1',
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: {
                    value: 'not-6343d5e4aba8c6d87d17ab6a',
                },
            });
            registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(getModelGroups)));
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getFinishedAutoTrainingJob())));
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText(/Your model has been successfully trained/i)).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test('Check that first successfully finished auto-training triggers "Successfully Trained Notification" and enables navigating to "Check Predictions" notification', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: { isEnabled: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
                    isEnabled: false,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: '60db493ed20945a0046f56ce',
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: {
                    value: 'job-1',
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: {
                    value: '6343d5e4aba8c6d87d17ab6a',
                },
            });
            registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(getModelGroups)));
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getFinishedAutoTrainingJob())));
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText(/Your model has been successfully trained/i)).toBeVisible();

            await page.getByRole('button', { name: 'Next', exact: true }).click();

            await expect(page.getByText(/Check predictions/i)).toBeVisible();
        });

        // eslint-disable-next-line max-len
        test('Check that first successfully finished auto-training triggers Successfully Trained Notification and closes Auto-training Scheduled Notification', async ({
            page,
            registerApiResponse,
        }) => {
            const jobsResponse = getScheduledAutoTrainingJob();

            registerStoreSettings(registerApiResponse, {
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: { value: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: { isEnabled: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: true },

                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: '60db493ed20945a0046f56ce',
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: {
                    value: jobsResponse.jobs[0].id,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: {
                    value: '6343d5e4aba8c6d87d17ab6a',
                },
            });
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(jobsResponse)));
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText(autoTrainingNotificationRegex)).toBeVisible();

            registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(getModelGroups)));
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getFinishedAutoTrainingJob())));

            // The UI polls the trained models every 30 seconds
            await expect(page.getByText(/Your model has been successfully trained/i)).toBeVisible({
                timeout: 30_000,
            });
            await expect(page.getByText(autoTrainingNotificationRegex)).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test(`Check that successfully trained notification will not be triggered if job id from first scheduled auto-training job doesn't match job id of the finished job`, async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                    isEnabled: false,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: '60db493ed20945a0046f56ce',
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: {
                    value: null,
                },
            });
            registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(getModelGroups)));
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getFinishedAutoTrainingJob())));
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText(/Your model has been successfully trained/i)).toBeHidden();
        });

        test('Check that second round of auto-training triggers auto-training toast notification', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                    isEnabled: false,
                },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
                    isEnabled: false,
                },
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: {
                    value: false,
                },
            });
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText(autoTrainingToastNotificationRegex)).toBeVisible();
        });

        // eslint-disable-next-line max-len
        test('Check that second round of auto-training toast notification will not be displayed if Successfully Trained Notification was not closed', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
                    isEnabled: false,
                },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_SUCCESSFULLY_TRAINED]: {
                    isEnabled: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: {
                    value: false,
                },
            });
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText('Auto-training round has been started')).toBeHidden();
        });

        // eslint-disable-next-line max-len
        test(`Check that successfully trained notification will not be triggered if training was triggered manually`, async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                    isEnabled: false,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: '662f70313090f9f2aa13b7ed',
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: {
                    value: null,
                },
            });
            registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(getModelGroups)));
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getFinishedTrainingJob())));
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByText(/Your model has been successfully trained/i)).toBeHidden();
        });

        test('Manually triggered training will not trigger Manually Scheduled Training Notification', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetProjectStatus', (_, res, ctx) => {
                return res(
                    // @ts-expect-error Issue ie openapi types
                    ctx.json(
                        getMockedProjectStatusDTO({
                            tasks: [
                                getMockedProjectStatusTask({
                                    id: '60db493fd20945a0046f56d2',
                                    title: 'Detection',
                                    ready_to_train: true,
                                }),
                                getMockedProjectStatusTask({
                                    id: '60db493fd20945a0046f56d6',
                                    title: 'Classification',
                                    ready_to_train: true,
                                }),
                            ],
                        })
                    )
                );
            });

            registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                res(ctx.status(200), ctx.json(projectConfigAutoTrainingOffMock))
            );
            await goToAnnotatorInActiveMode(page);

            await startTaskTraining(page);
            await page.getByRole('button', { name: /start/i }).click();

            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledTrainingJob())));
            await expect(page.getByText(manualTrainingCreditSystemToastNotificationRegex)).toBeHidden();
        });
    });

    test.describe('Check notifications with enabled FEATURE_FLAG_CREDIT_SYSTEM', () => {
        test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

        test('Check that clicking "Dismiss all" also dismisses credit system notifications', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                res(ctx.status(200), ctx.json(projectConfigAutoTrainingOnMock))
            );
            registerStoreSettings(registerApiResponse, {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
                    isEnabled: true,
                },
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: {
                    isEnabled: true,
                },
            });
            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));
            await goToAnnotatorInActiveMode(page);

            await expect(page.getByRole('heading', { name: autoTrainingCreditSystemModalRegex })).toBeVisible();

            await page.getByRole('button', { name: 'Dismiss' }).click();

            await expect(
                page.getByTestId('popover').filter({ hasText: autoTrainingCreditSystemNotificationRegex })
            ).toBeVisible();

            // first click closes the "The auto-training job has ..." notification that is popover
            await page.getByTestId('annotatorActiveSet-more-btn-id').click();

            await page.getByTestId('annotatorActiveSet-more-btn-id').click();
            await page.getByRole('menuitem', { name: 'Dismiss all' }).click();
            await page.reload();
            await expect(
                page.getByTestId('popover').filter({ hasText: autoTrainingCreditSystemNotificationRegex })
            ).toBeHidden();
        });

        test.describe('with auto-training ON', () => {
            test.beforeEach(async ({ registerApiResponse }) => {
                registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                    res(ctx.status(200), ctx.json(projectConfigAutoTrainingOnMock))
                );
                registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
                    res(ctx.json({ incoming: 10, available: 100 }))
                );
            });

            // eslint-disable-next-line max-len
            test('Auto-training Credit System modal will not be triggered if not enough credits to start auto-training', async ({
                page,
                registerApiResponse,
            }) => {
                registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
                    res(ctx.json({ incoming: 10, available: 0 }))
                );
                registerStoreSettings(registerApiResponse, {
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: {
                        isEnabled: true,
                    },
                });

                await goToAnnotatorInActiveMode(page);

                await expect(page.getByRole('heading', { name: autoTrainingCreditSystemModalRegex })).toBeHidden();
            });

            // eslint-disable-next-line max-len
            test('After first auto-training starts, Credit System Modal and Credit System Notification should appear, and "Continue Annotating Notification" should not be shown', async ({
                page,
                registerApiResponse,
            }) => {
                registerStoreSettings(registerApiResponse, {
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: {
                        isEnabled: true,
                    },
                });

                await goToAnnotatorInActiveMode(page);
                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));

                await expect(page.getByRole('heading', { name: autoTrainingCreditSystemModalRegex })).toBeVisible();
                await expect(page.getByRole('button', { name: 'Dismiss' })).toBeEnabled();

                await page.getByRole('button', { name: 'Dismiss' }).click();

                await expect(page.getByRole('heading', { name: autoTrainingCreditSystemModalRegex })).toBeHidden();
                await expect(page.getByText(autoTrainingCreditSystemNotificationRegex)).toBeVisible();
            });

            test('Check that second round of auto training triggers auto-training credit toast notification', async ({
                page,
                registerApiResponse,
            }) => {
                registerStoreSettings(registerApiResponse, {
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: {
                        isEnabled: false,
                    },
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: {
                        isEnabled: false,
                    },
                });
                await goToAnnotatorInActiveMode(page);
                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));

                await expect(page.getByText('Auto-training round has been started, 6 credits deducted.')).toBeVisible();
            });

            // eslint-disable-next-line max-len
            test('Check that second round of auto training will not trigger Auto-training Credit System Toast notification if Successfully Trained notification was not closed', async ({
                page,
                registerApiResponse,
            }) => {
                registerStoreSettings(registerApiResponse, {
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: {
                        isEnabled: false,
                    },
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: {
                        isEnabled: false,
                    },
                });
                await goToAnnotatorInActiveMode(page);
                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));

                await expect(page.getByText(autoTrainingCreditSystemToastNotificationRegex)).toBeVisible();
            });

            test('Manually triggered training should trigger Manual Training Credit Deduction Toast', async ({
                page,
                registerApiResponse,
            }) => {
                await goToAnnotatorInActiveMode(page);
                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledTrainingCostJob([]))));

                await expect(page.getByText(manualTrainingCreditSystemToastNotificationRegex)).toBeVisible();
            });

            test('Credit System Notification stays hidden after being closed by the user', async ({
                page,
                registerApiResponse,
            }) => {
                registerStoreSettings(registerApiResponse, {
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: false },
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: { isEnabled: true },
                    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: project.id },
                });
                registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));
                await goToAnnotatorInActiveMode(page);

                await expect(page.getByText(autoTrainingCreditSystemNotificationRegex)).toBeVisible();

                await page.getByRole('button', { name: /close first user experience notification/i }).click();
                await page.reload();

                await expect(
                    page.getByRole('button', { name: /close first user experience notification/i })
                ).toBeHidden();
            });

            // eslint-disable-next-line max-len
            test('Auto-training Credits Modal stays hidden after being closed by the user and opens Auto-training Credits Notification', async ({
                page,
                registerApiResponse,
            }) => {
                registerStoreSettings(registerApiResponse, {
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: true },
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: { isEnabled: false },
                });
                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingCostJob([]))));
                await goToAnnotatorInActiveMode(page);

                await expect(page.getByText(autoTrainingCreditSystemModalRegex)).toBeVisible();

                await page.getByRole('button', { name: /dismiss/i }).click();
                await page.reload();

                await expect(page.getByText(autoTrainingCreditSystemModalRegex)).toBeHidden();
                await expect(page.getByText(autoTrainingCreditSystemNotificationRegex)).toBeVisible();
            });
        });

        test.describe('with auto-training OFF', () => {
            test.beforeEach(async ({ registerApiResponse }) => {
                registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
                    res(ctx.json({ incoming: 10, available: 100 }))
                );
                registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
                    res(ctx.status(200), ctx.json(projectConfigAutoTrainingOffMock))
                );
            });

            test('Credit system modal will not appear when auto-training is off', async ({
                page,
                registerApiResponse,
            }) => {
                registerStoreSettings(registerApiResponse, {
                    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: {
                        isEnabled: true,
                    },
                });
                await goToAnnotatorInActiveMode(page);
                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledAutoTrainingJob())));

                await expect(page.getByRole('heading', { name: 'Accelerate the time-to-model' })).toBeHidden();
            });

            test('Manual Training Credit Deduction notification will pop up after scheduling job', async ({
                page,
                registerApiResponse,
            }) => {
                registerApiResponse('GetProjectStatus', (_, res, ctx) => {
                    return res(
                        // @ts-expect-error Issue ie openapi types
                        ctx.json(
                            getMockedProjectStatusDTO({
                                tasks: [
                                    getMockedProjectStatusTask({
                                        id: '60db493fd20945a0046f56d2',
                                        title: 'Detection',
                                        ready_to_train: true,
                                    }),
                                    getMockedProjectStatusTask({
                                        id: '60db493fd20945a0046f56d6',
                                        title: 'Classification',
                                        ready_to_train: true,
                                    }),
                                ],
                            })
                        )
                    );
                });

                await goToAnnotatorInActiveMode(page);
                await startTaskTraining(page);

                await page.getByRole('button', { name: /credits to consume/i }).click();
                await expect(page.getByText(manualTrainingCreditSystemToastNotificationRegex)).toBeHidden();

                registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(getScheduledTrainingCostJob([]))));

                await expect(page.getByText(manualTrainingCreditSystemToastNotificationRegex)).toBeVisible();
            });
        });
    });
});
