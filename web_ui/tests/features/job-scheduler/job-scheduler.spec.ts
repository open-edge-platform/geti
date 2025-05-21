// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';
import { ResponseComposition, RestContext } from 'msw';

import { OpenApiRequest } from '../../../src/core/server/types';
import { test } from '../../fixtures/base-test';
import { mockedJobsResponse, mockedJobsRunningResponse } from './mocks';
import { openJobSchedulerModal } from './utils';

const waitForReady = async (page: Page): Promise<void> => {
    await expect(page.getByLabel('Loading...').last()).toBeHidden({ timeout: 10000 });
};

test.describe('JobScheduler', (): void => {
    test('Layout', async ({ page }): Promise<void> => {
        await page.goto('/');
        await openJobSchedulerModal(page);

        await expect(page.getByRole('combobox', { name: 'Job scheduler filter project' })).toBeVisible();
        await expect(page.getByRole('combobox', { name: 'Job scheduler filter user' })).toBeVisible();
        await expect(page.getByRole('combobox', { name: 'Job scheduler filter job type' })).toBeVisible();

        await expect(page.getByRole('button', { name: 'Job scheduler action expand' })).toBeVisible();

        await expect(page.getByRole('tab', { name: /Running jobs/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /Finished jobs/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /Scheduled jobs/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /Cancelled jobs/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /Failed jobs/i })).toBeVisible();
    });

    test('Search params', async ({ page }): Promise<void> => {
        await page.goto('/');
        await openJobSchedulerModal(page);

        const expectedParams = 'resourceId=62946c61003ddb3967f14750&resourceType=project';

        const requestPromise = page.waitForRequest(async (res) => res.url().includes('resourceId'));
        await page
            .getByLabel(/Show suggestions/)
            .first()
            .click();

        await page.getByRole('option', { name: /Card detection/ }).click();

        const request = await requestPromise;

        expect(await request.url()).toContain(expectedParams);
    });

    test('Badges', async ({ registerApiResponse, page }): Promise<void> => {
        registerApiResponse(
            'GetJobs',
            (_: OpenApiRequest<'GetJobs'>, res: ResponseComposition<Record<string, unknown>>, ctx: RestContext) =>
                res(ctx.json(mockedJobsResponse))
        );

        await page.goto('/');
        await openJobSchedulerModal(page);

        await waitForReady(page);

        await expect(page.getByTestId('number-badge-running-jobs-value').last()).toHaveText('1');
        await expect(page.getByTestId('number-badge-finished-jobs-value')).toHaveText('3');
        await expect(page.getByTestId('number-badge-scheduled-jobs-value')).toHaveText('2');
        await expect(page.getByTestId('number-badge-cancelled-jobs-value')).toBeHidden();
        await expect(page.getByTestId('number-badge-failed-jobs-value')).toHaveText('4');
    });

    test('Empty tab', async ({ registerApiResponse, page }): Promise<void> => {
        registerApiResponse(
            'GetJobs',
            (_: OpenApiRequest<'GetJobs'>, res: ResponseComposition<Record<string, unknown>>, ctx: RestContext) =>
                res(ctx.json({ ...mockedJobsResponse, jobs: [] }))
        );

        await page.goto('/');
        await openJobSchedulerModal(page);

        await waitForReady(page);

        await expect(page.getByText('There are no running jobs')).toBeVisible();
    });

    test('Tab content', async ({ registerApiResponse, page }): Promise<void> => {
        registerApiResponse(
            'GetJobs',
            (_: OpenApiRequest<'GetJobs'>, res: ResponseComposition<Record<string, unknown>>, ctx: RestContext) =>
                res(ctx.json(mockedJobsResponse))
        );

        await page.goto('/');
        await openJobSchedulerModal(page);

        await waitForReady(page);

        const optimizationJob = page.getByTestId('job-scheduler-65100ac2add2d0ffd46da49f');
        await expect(optimizationJob).toContainText('Optimization');
        await expect(optimizationJob).toContainText('Project: model_test_result_flowers');
        await expect(optimizationJob).toContainText('Architecture: MaskRCNN-ResNet50');
        await expect(optimizationJob).toContainText('Optimization type: POT');
        await expect(optimizationJob).toContainText(/Created: \d{2}:09:06, 24 Sep 23/);

        const testingJob = page.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495');
        await expect(testingJob).toContainText('Model testing');
        await expect(testingJob).toContainText('Project: Project');
        await expect(testingJob).toContainText('Architecture: Lite-HRNet-18-mod2');
        await expect(testingJob).toContainText('Optimization type: MO');
        await expect(testingJob).toContainText('Precision: FP16');
        await expect(testingJob).toContainText(/Created: \d{2}:31:08, 14 Sep 23/);

        const trainingJob = page.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494');
        await expect(trainingJob).toContainText('Training');
        await expect(trainingJob).toContainText('Project: Tiff images');
        await expect(trainingJob).toContainText('Architecture: MaskRCNN-ResNet50');
        await expect(trainingJob).toContainText('Task: Instance segmentation');
        await expect(trainingJob).toContainText(/Created: \d{2}:44:45, 13 Sep 23/);
    });

    test('Running step', async ({ registerApiResponse, page }): Promise<void> => {
        registerApiResponse(
            'GetJobs',
            (_: OpenApiRequest<'GetJobs'>, res: ResponseComposition<Record<string, unknown>>, ctx: RestContext) =>
                res(ctx.json(mockedJobsRunningResponse))
        );

        await page.goto('/');
        await openJobSchedulerModal(page);

        await page.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-action-expand').click();

        const step = page.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-step-1-retrieve-train-data');
        const stateIcon = step.getByTestId(
            'job-scheduler-65015a5dadd2d0ffd46da494-step-1-retrieve-train-data-state-icon'
        );

        await expect(stateIcon.getByLabel('Loading...')).toBeVisible();

        await expect(
            step.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-step-1-retrieve-train-data-name')
        ).toHaveText('Retrieve train data (1 of 9)');

        await expect(
            step.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-step-1-retrieve-train-data-progress')
        ).toHaveText('65%');
    });

    test.describe('Other steps', (): void => {
        test.beforeEach(async ({ registerApiResponse, page }): Promise<void> => {
            registerApiResponse(
                'GetJobs',
                (_: OpenApiRequest<'GetJobs'>, res: ResponseComposition<Record<string, unknown>>, ctx: RestContext) =>
                    res(ctx.json(mockedJobsResponse))
            );

            await page.goto('/');
            await openJobSchedulerModal(page);
            await waitForReady(page);
        });

        test('Waiting', async ({ page }): Promise<void> => {
            await page.getByTestId('job-scheduler-65100ac2add2d0ffd46da49f-action-expand').click();

            const step = page.getByTestId('job-scheduler-65100ac2add2d0ffd46da49f-step-2-optimizing-model');
            const stateIcon = step.getByTestId(
                'job-scheduler-65100ac2add2d0ffd46da49f-step-2-optimizing-model-state-icon'
            );

            await expect(stateIcon.getByRole('img')).toHaveClass(/iconWaiting/i);

            await expect(
                step.getByTestId('job-scheduler-65100ac2add2d0ffd46da49f-step-2-optimizing-model-name')
            ).toHaveText('Optimizing model (2 of 3)');

            await expect(
                step.getByTestId('job-scheduler-65100ac2add2d0ffd46da49f-step-2-optimizing-model-progress')
            ).toHaveText('Waiting...');
        });

        test('Finished', async ({ page }): Promise<void> => {
            await page.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-action-expand').click();

            const step = page.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-step-1-creating-testing-dataset');
            const stateIcon = step.getByTestId(
                'job-scheduler-6502eefcadd2d0ffd46da495-step-1-creating-testing-dataset-state-icon'
            );

            await expect(stateIcon.getByRole('img')).toHaveClass(/iconFinished/i);

            await expect(
                step.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-step-1-creating-testing-dataset-name')
            ).toHaveText('Creating testing dataset (1 of 3): Testing dataset created');

            await expect(
                step.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-step-1-creating-testing-dataset-progress')
            ).toHaveText('100%');
        });

        test('Skipped', async ({ page }): Promise<void> => {
            await page.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-action-expand').click();

            const step = page.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-step-4-pre-evaluate-model-if-exists');
            const stateIcon = step.getByTestId(
                'job-scheduler-65015a5dadd2d0ffd46da494-step-4-pre-evaluate-model-if-exists-state-icon'
            );

            await expect(stateIcon.getByRole('img')).toHaveClass(/iconSkipped/i);

            await expect(
                step.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-step-4-pre-evaluate-model-if-exists-name')
            ).toHaveText('Pre-evaluate model if exists (4 of 9)');
            await expect(
                step.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-step-4-pre-evaluate-model-if-exists-message')
            ).toHaveText('No previous model found for the project.');
            await expect(
                step.getByTestId('job-scheduler-65015a5dadd2d0ffd46da494-step-4-pre-evaluate-model-if-exists-progress')
            ).toHaveText('Skipped');
        });

        test('Failed', async ({ page }): Promise<void> => {
            await page.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-action-expand').click();

            const step = page.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-step-3-evaluating-results');
            const stateIcon = step.getByTestId(
                'job-scheduler-6502eefcadd2d0ffd46da495-step-3-evaluating-results-state-icon'
            );

            await expect(stateIcon.getByRole('img')).toHaveClass(/iconFailed/i);

            await expect(
                step.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-step-3-evaluating-results-name')
            ).toHaveText('Evaluating results (3 of 3)');

            await expect(
                step.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-step-3-evaluating-results-message')
            ).toHaveText('Results evaluated failed');

            await expect(
                step.getByTestId('job-scheduler-6502eefcadd2d0ffd46da495-step-3-evaluating-results-progress')
            ).toHaveText('Failed');
        });
    });
});
