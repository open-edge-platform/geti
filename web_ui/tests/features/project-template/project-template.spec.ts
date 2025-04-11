// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect } from '@playwright/test';

import { test } from '../../fixtures/base-test';
import { project as keypointProject, labels } from '../../mocks/keypoint-detection/mocks';
import { project as segmentationProject } from '../../mocks/segmentation/mocks';

const LABELS_URL =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/labels';
const TEMPLATE_URL =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/template';

test.describe('Template editor', () => {
    test('projects other than keypoint are redirected to the labels page', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json(segmentationProject));
        });
        await page.goto(TEMPLATE_URL, { timeout: 20000 });

        await expect(page.getByRole('button', { name: 'Edit labels' })).toBeVisible();
        expect(page.url()).toContain(LABELS_URL);
    });

    test('keypoint projects are redirected to the template page', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json(keypointProject));
        });

        await page.goto(LABELS_URL, { timeout: 20000 });

        await expect(page.getByRole('button', { name: /^Update Template$/ })).toBeVisible();
        expect(page.url()).toContain(TEMPLATE_URL);
    });

    test('deletion of points is disabled', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json(keypointProject));
        });

        await page.goto(TEMPLATE_URL, { timeout: 20000 });

        await expect(page.getByRole('button', { name: /^Update Template$/ })).toBeVisible();

        await page.getByLabel(`keypoint ${labels.head.name} anchor`).click();

        await expect(
            page.getByRole('button', { name: `toolbar delete keypoint ${labels.head.name}` })
        ).not.toBeInViewport();

        await expect(page.getByLabel(new RegExp(`^delete keypoint ${labels.head.name}$`))).not.toBeInViewport();
    });

    test('add points is disabled', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json(keypointProject));
        });

        await page.goto(TEMPLATE_URL, { timeout: 20000 });

        await expect(page.getByRole('button', { name: 'Update Template' })).toBeVisible();

        await page.getByLabel(`keypoint ${labels.head.name} anchor`).click();

        await expect(page.getByLabel('drawing box')).not.toBeInViewport();
    });

    test.describe('show unsaved changes popover after modifying the template', () => {
        test('stay on page', async ({ page, templateManagerPage, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
                return res(ctx.status(200), ctx.json(keypointProject));
            });

            await page.goto(TEMPLATE_URL, { timeout: 20000 });

            await expect(page.getByRole('button', { name: 'Update Template' })).toBeDisabled();

            const point = page.getByLabel(`keypoint ${labels.head.name} anchor`);
            const initialPosition = await templateManagerPage.getPosition(point);
            const newPosition = { x: initialPosition.x + 100, y: initialPosition.y };
            await templateManagerPage.movePointTo(page, point, newPosition);

            await expect(page.getByRole('button', { name: 'Update Template' })).toBeEnabled();

            await page.getByRole('link', { name: 'Deployments' }).click();
            await expect(page.getByRole('heading', { name: 'Unsaved changes' })).toBeVisible();

            await page.getByRole('button', { name: 'Stay on page' }).click();

            expect(page.url()).toContain('/template');
        });

        test('leave page', async ({ page, templateManagerPage, registerApiResponse }) => {
            registerApiResponse('GetProjectInfo', (_req, res, ctx) => {
                return res(ctx.status(200), ctx.json(keypointProject));
            });

            await page.goto(TEMPLATE_URL, { timeout: 20000 });

            await expect(page.getByRole('button', { name: 'Update Template' })).toBeDisabled();

            const point = page.getByLabel(`keypoint ${labels.head.name} anchor`);
            const initialPosition = await templateManagerPage.getPosition(point);
            const newPosition = { x: initialPosition.x + 100, y: initialPosition.y };
            await templateManagerPage.movePointTo(page, point, newPosition);

            await expect(page.getByRole('button', { name: 'Update Template' })).toBeEnabled();

            await page.getByRole('link', { name: 'Deployments' }).click();
            await expect(page.getByRole('heading', { name: 'Unsaved changes' })).toBeVisible();

            await page.getByRole('button', { name: 'Leave' }).click();
            expect(page.url()).toContain('/deployments');
        });
    });
});
