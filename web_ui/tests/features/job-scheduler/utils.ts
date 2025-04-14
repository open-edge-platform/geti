// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { JobDatasetDTO } from '../../../src/core/jobs/dtos/jobs-dto.interface';

export const openJobSchedulerModal = async (page: Page): Promise<void> => {
    await page.getByRole('button', { name: 'Jobs in progress' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
};

export const cancelJobFromJobScheduler = async (job: JobDatasetDTO, page: Page) => {
    await openJobSchedulerModal(page);
    await page
        .getByLabel('Job management tabs')
        .getByText(/Scheduled jobs/)
        .click();
    await expect(page.getByText(job.name)).toBeVisible();
    await page.getByTestId(`job-scheduler-${job.id}-action-cancel`).click();
    await expect(page.getByText(`Are you sure you want to cancel job "${job.name}"?`)).toBeVisible();
    await page.getByRole('button', { name: 'Cancel job', exact: true }).click();
};
