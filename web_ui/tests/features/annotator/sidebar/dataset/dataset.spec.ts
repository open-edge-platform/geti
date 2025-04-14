// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { test } from '../../../../fixtures/base-test';
import { VIEWPORT_TYPE } from '../../../../utils/test-type';
import { project } from './../../../../mocks/segmentation/mocks';

export const annotatorUrl =
    // eslint-disable-next-line max-len
    'http://localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/datasets/6101254defba22ca453f11cc/annotator';

test.describe('dataset - active set', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.status(404)));

        registerApiResponse('FilterMedia', (_req, res, ctx) =>
            res(
                ctx.status(200),
                ctx.json({
                    media: [],
                    next_page: '',
                    total_matched_images: 0,
                    total_matched_videos: 0,
                    total_matched_video_frames: 0,
                    total_images: 0,
                    total_videos: 0,
                })
            )
        );
    });

    test('Empty dataset', async ({ page }) => {
        await page.goto(annotatorUrl);

        await expect(
            page.getByText(
                'Dataset is empty Please select a different dataset or upload new media items to start annotating.'
            )
        ).toBeVisible();

        await expect(page.getByRole('heading', { name: 'Dataset is empty' })).toBeVisible();
        await expect(
            page.getByText('Please select a different dataset or upload new media item to annotate more.')
        ).toBeVisible();
    });

    test(`${VIEWPORT_TYPE.MOBILE} Check if dataset view mode stays the same after reopening the panel`, async ({
        page,
    }) => {
        await page.goto(annotatorUrl);

        await page.getByRole('button', { name: 'dataset accordion' }).click();
        await page.getByRole('button', { name: 'View mode' }).click();
        await page.getByText('Details').click();
        await expect(page.getByText('Details')).toBeHidden();

        //hide panel
        await page.getByRole('button', { name: 'annotation list' }).click();

        await page.getByRole('button', { name: 'dataset accordion' }).click();
        await page.getByRole('button', { name: 'View mode' }).click();
        await expect(page.getByRole('menuitemradio', { name: 'Details' })).toHaveAttribute('aria-checked', 'true');
    });

    test('Empty active set', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetActiveDataset', (_req, res, ctx) => res(ctx.status(200), ctx.json({ active_set: [] })));

        await page.goto(annotatorUrl);
        const datasetMenuButton = page.getByRole('button', { name: /dataset/i });

        await expect(datasetMenuButton).toBeVisible();
        await datasetMenuButton.click();

        await page.getByRole('option', { name: /active set/i }).click();

        await expect(
            page.getByText(
                'Active set is empty Please select a different dataset or upload new media items to start annotating.'
            )
        ).toBeVisible();

        await expect(page.getByRole('heading', { name: 'Active set is empty' })).toBeVisible();
        await expect(
            page.getByText('Please select a different dataset or upload new media item to annotate more.')
        ).toBeVisible();
    });

    test('Selected empty active set', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetActiveDataset', (_req, res, ctx) => res(ctx.status(200), ctx.json({ active_set: [] })));

        await page.goto(`${annotatorUrl}?active=true`);

        await expect(
            page.getByText(
                'Active set is empty Please select a different dataset or upload new media items to start annotating.'
            )
        ).toBeVisible();

        await expect(page.getByRole('heading', { name: 'Active set is empty' })).toBeVisible();
        await expect(
            page.getByText('Please select a different dataset or upload new media item to annotate more.')
        ).toBeVisible();
    });
});
