// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { expect, Page } from '@playwright/test';

import {
    getMockedProjectStatusDTO,
    getMockedProjectStatusTask,
} from '../../../src/test-utils/mocked-items-factory/mocked-project';
import { test } from '../../fixtures/base-test';
import { getScheduledTrainingCostJob, getScheduledTrainingJob, projectConfigAutoTrainingOffMock } from './mocks';

const ANNOTATOR_URL = paths.project.annotator.image({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: '6101a',
    projectId: '6101b',
    datasetId: '6101c',
    imageId: '6101d',
});

const notEnoughCreditsRegex = /you don’t have enough credits to train the model/i;
const creditNotificationRegex = /the model training has been started, 6 credits deducted./i;

const startTaskTraining = async (page: Page) => {
    await page.getByRole('button', { name: /Active learning configuration/i }).click();
    await page.getByRole('button', { name: /start training sample detection task/i }).click();
};

test.use({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

test.beforeEach(async ({ registerApiResponse }) => {
    registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
        res(ctx.json({ incoming: 10, available: 100 }))
    );
    registerApiResponse('GetFullConfiguration', (_, res, ctx) =>
        res(ctx.status(200), ctx.json(projectConfigAutoTrainingOffMock))
    );
});

test.describe('manual training notification - autotraining off', () => {
    test('"not enough credits" modal pops up', async ({ page, registerApiResponse }) => {
        registerApiResponse('get_balance_api_v1_organizations__org_id__balance_get', (_, res, ctx) =>
            res(ctx.json({ incoming: 10, available: 0 }))
        );

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

        await page.goto(ANNOTATOR_URL);

        await startTaskTraining(page);

        await expect(page.getByText(notEnoughCreditsRegex)).toBeVisible();
        await expect(page.getByText(creditNotificationRegex)).toBeHidden();
    });
});

test.describe('cancel training jobs', () => {
    const closeAutoTrainingAndOpenJobs = async (page: Page) => {
        await page.mouse.click(0, 0);

        await page.getByRole('button', { name: /Jobs in progress/i }).click();
        await page.getByTestId('job-scheduler-job-1-action-cancel').click();
    };

    test.beforeEach(({ registerApiResponse }) => {
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
    });

    test('refund warning pops up', async ({ page, registerApiResponse }) => {
        await page.goto(ANNOTATOR_URL);
        const amountConsumed = 10;

        await startTaskTraining(page);
        await page.getByRole('button', { name: /credits to consume/i }).click();
        registerApiResponse('GetJobs', (_, res, ctx) =>
            res(ctx.json(getScheduledTrainingCostJob([{ unit: '10', amount: amountConsumed, consuming_date: '123' }])))
        );

        await closeAutoTrainingAndOpenJobs(page);

        await expect(
            page.getByText(`Are you sure you want to cancel job "Mocked task job" and lose ${amountConsumed} credits?`)
        ).toBeVisible();
    });

    test('cancel confirmation pops up', async ({ page, registerApiResponse }) => {
        const mockedJob = getScheduledTrainingJob();
        await page.goto(ANNOTATOR_URL);

        await startTaskTraining(page);
        await page.getByRole('button', { name: /credits to consume/i }).click();
        registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(mockedJob)));

        await closeAutoTrainingAndOpenJobs(page);

        await expect(page.getByText('Are you sure you want to cancel job "Mocked task job"?')).toBeVisible();
    });
});
