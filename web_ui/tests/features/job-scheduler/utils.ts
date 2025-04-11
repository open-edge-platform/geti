// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
