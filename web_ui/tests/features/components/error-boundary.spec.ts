// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';

import { expect, test } from '../../fixtures/base-test';

const annotatorUrl = paths.project.annotator.image({
    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
    workspaceId: 'workspace-id',
    projectId: 'project',
    datasetId: 'in-memory-dataset',
    imageId: '613a23866674c43ae7a777aa',
});

// We show a loading indicator while loading the user, and if the query fails we retry 3 times
const RETRY_TIMEOUT = { timeout: 30_000 };

test.describe('Error boundary', () => {
    test('project layout', async ({ page, registerApiExample, baseURL }) => {
        registerApiExample('GetProjectInfo', 'Project not found response', 404);

        // check that error handling works when project isn't loaded
        await page.goto(
            // eslint-disable-next-line max-len
            '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/60ec6bbfb98caeb87e34306e/projects/x/datasets/6101254defba22ca453f11cc/media'
        );

        await expect(
            page.getByRole('heading', { name: /Could not find project with id 60ec6bbfb98caeb87e34306e/i })
        ).toBeVisible(RETRY_TIMEOUT);
        await page.getByRole('button', { name: /go back to home/i }).click();
        expect(page.url()).toBe(`${baseURL}/`);
    });

    test('annotator layout', async ({ page, registerApiExample }) => {
        registerApiExample('GetImageAnnotation', '', 404);
        registerApiExample('DownloadFullImage', '', 404);

        await page.goto(annotatorUrl);

        await expect(page.getByRole('heading', { name: /failed loading media item/i })).toBeVisible(RETRY_TIMEOUT);
    });

    test('forbidden', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.status(403));
        });

        await page.goto(annotatorUrl);

        await expect(page.getByRole('heading', { name: /Forbidden/i })).toBeVisible(RETRY_TIMEOUT);
    });

    test('it does not show a forbidden modal when fetching user info', async ({ page, registerApiResponse }) => {
        registerApiResponse('User_get_by_id', (_, res, ctx) => {
            return res(ctx.status(403));
        });

        await page.goto(
            // eslint-disable-next-line max-len
            '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/610123e6efba22ca453f11bd/datasets/6101254defba22ca453f11cc/media'
        );

        const image = page.getByTestId('dummy_images(584x331)');
        await expect(image).toBeVisible();

        await page.mouse.move(0, 0);
        await image.hover();

        await expect(page.getByText('Owner: Unknown user')).toBeVisible(RETRY_TIMEOUT);
        await expect(page.getByText('Last annotator: Unknown user')).toBeVisible(RETRY_TIMEOUT);
        await expect(page.getByRole('dialog')).toBeHidden();
    });

    test('service unavailable', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.status(503));
        });

        await page.goto(annotatorUrl);

        await expect(page.getByRole('heading', { name: /We are experiencing technical difficulties/i })).toBeVisible(
            RETRY_TIMEOUT
        );
    });

    test('too many requests', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.status(429));
        });

        await page.goto(annotatorUrl);

        await expect(page.getByRole('heading', { name: /We are experiencing technical difficulties/i })).toBeVisible(
            RETRY_TIMEOUT
        );
    });

    test('bad request', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.status(400));
        });

        await page.goto(annotatorUrl);

        await expect(page.getByRole('heading', { name: /bad request/i })).toBeVisible(RETRY_TIMEOUT);
    });

    test('internal server error', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.status(500));
        });

        await page.goto(annotatorUrl);

        await expect(page.getByRole('heading', { name: /Internal server error/i })).toBeVisible(RETRY_TIMEOUT);
    });

    test('Unauthenticated', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.status(401));
        });

        await page.goto(annotatorUrl);

        await expect(page.getByRole('heading', { name: /Unauthenticated/i })).toBeVisible(RETRY_TIMEOUT);
    });
});
