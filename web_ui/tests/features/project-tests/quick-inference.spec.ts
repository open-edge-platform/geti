// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as path from 'path';

import { cloneDeep } from 'lodash-es';

import { expect, test } from '../../fixtures/base-test';
import { predictionAnnotationsResponse, project } from '../../mocks/classification/mocks';
import { annotatorUrl } from '../../mocks/segmentation/mocks';
import { getDirname } from '../../utils/get-dirname';
import { expectAGlobalAnnotationToExist } from './expect';

const imagePath = path.resolve(getDirname(import.meta.url), '../../../src/assets/tests-assets/antelope.png');
const explanationLabel = { name: 'saddled', id: '6101254defba22ca453f11c8' };
const explanation = {
    // eslint-disable-next-line max-len
    binary: '/9j/4AAQSkZJRgABAQAAbABqAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAHAAoDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAAAAMF/8QAIRAAAQMEAQUAAAAAAAAAAAAAAgEDBQAEITEGBxESUaH/xAAVAQEBAAAAAAAAAAAAAAAAAAAGB//EACIRAAEDAwMFAAAAAAAAAAAAAAECAwQhMUEABRESIlFxkf/aAAwDAQACEQMRAD8Anb8SjpGMYB+UcV60BRUVthIFMtYXfqsk+kTvmXaXbTOlZXH2lKVvTpkZ9QS6SDghNLGnbzk3J1OTukhpHS3wK3859fANf//Z',
    id: '63ea345912a647811e26139f',
    label_id: explanationLabel.id,
    name: '',
    roi: {
        id: '63ea345912a647811e26139e',
        shape: {
            type: 'RECTANGLE',
            x: 0,
            y: 0,
            width: 940,
            height: 629,
        },
    },
};

test.beforeEach(async ({ page, registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        return res(ctx.json(cloneDeep(project)));
    });

    registerApiResponse('GetImagePrediction', async (_, res, ctx) => {
        return res(ctx.status(200), ctx.json(predictionAnnotationsResponse));
    });

    registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
        return res(ctx.status(200), ctx.json({ predictions: predictionAnnotationsResponse.annotations }));
    });

    await page.goto(
        // eslint-disable-next-line max-len
        '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/63283aedc80c9c686fd3b1e6/tests/live-prediction'
    );
});

test('Quick inference', async ({ page, quickInferencePage }) => {
    await quickInferencePage.uploadImage(imagePath);

    await expectAGlobalAnnotationToExist(page);

    // check uploading another image using full screen mode works
    await quickInferencePage.openFullscreen();

    await quickInferencePage.uploadImage(imagePath);

    await expectAGlobalAnnotationToExist(page.getByRole('dialog'));

    await quickInferencePage.closeFullscreen();
});

test.describe('Explanation', () => {
    test('Quick inference retrieves with explanation', async ({ page, quickInferencePage, registerApiResponse }) => {
        await quickInferencePage.uploadImage(imagePath);

        // Mock with an explanation response...
        registerApiResponse('GetImagePrediction', async (_, res, ctx) => {
            return res(ctx.status(200), ctx.json({ ...predictionAnnotationsResponse, maps: [explanation] }));
        });
        registerApiResponse('GetSingleExplanation', async (_, res, ctx) => {
            return res(
                ctx.status(200),
                ctx.json({
                    maps: [{ data: explanation.binary, label_id: explanation.label_id, id: explanation.id }],
                })
            );
        });

        await quickInferencePage.toggleExplanation();
        await expect(
            page.getByRole('button', { name: `${explanationLabel.name} show explanations dropdown` })
        ).toBeVisible();

        const explanationImage = page.getByTestId('explanation-image');
        await expect(explanationImage).toBeVisible();
    });

    test('Quick inference retrieves with empty explanation', async ({
        page,
        quickInferencePage,
        registerApiResponse,
    }) => {
        await quickInferencePage.uploadImage(imagePath);

        // Mock with a map response...
        registerApiResponse('GetImagePrediction', async (_, res, ctx) => {
            return res(ctx.status(200), ctx.json({ ...predictionAnnotationsResponse, maps: [] }));
        });

        registerApiResponse('GetSingleExplanation', async (_, res, ctx) => {
            return res(ctx.status(200), ctx.json({ maps: [] }));
        });

        await quickInferencePage.toggleExplanation();
        const dropdown = page.getByRole('button', { name: /show explanations dropdown/i });
        const parent = dropdown.locator('..');

        await parent.hover();
        await expect(page.getByText('No explanations were generated')).toBeVisible();

        await expect(dropdown).toBeDisabled();
        await expect(page.getByRole('button', { name: /opacity slider button/i })).toBeDisabled();
    });
});

test.describe('With a slow inference server', () => {
    test.beforeEach(async ({ registerApiResponse, openApi }) => {
        let failedOnce = false;

        registerApiResponse('GetImagePrediction', async (_, res, ctx) => {
            if (failedOnce) {
                return res(ctx.status(200), ctx.json(predictionAnnotationsResponse));
            }

            failedOnce = true;
            const { mock, status } = openApi.mockResponseForOperation('GetImagePrediction', {
                code: 503,
            });
            return res(ctx.status(status), ctx.json(mock));
        });

        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            if (failedOnce) {
                return res(ctx.status(200), ctx.json({ predictions: predictionAnnotationsResponse.annotations }));
            }
            failedOnce = true;
            return res(ctx.status(400));
        });
    });

    test('Quick inference without an inference server', async ({ page, quickInferencePage }) => {
        await quickInferencePage.uploadImage(imagePath);

        expect(await quickInferencePage.getAlertMessage()).toContain('Retrieving inference results may take some time');

        await expectAGlobalAnnotationToExist(page);
    });

    test('Full screen inference server', async ({ page, quickInferencePage }) => {
        await quickInferencePage.uploadImage(imagePath);
        await quickInferencePage.openFullscreen();

        expect(await quickInferencePage.getAlertMessage()).toContain('Retrieving inference results may take some time');

        const dialog = page.getByRole('dialog');
        await expectAGlobalAnnotationToExist(dialog);
    });

    test('Adjusting canvas settings should not persist configuration changes', async ({ page, quickInferencePage }) => {
        await quickInferencePage.uploadImage(imagePath);
        await quickInferencePage.openFullscreen();

        expect(await quickInferencePage.getAlertMessage()).toContain('Retrieving inference results may take some time');

        const dialog = page.getByRole('dialog');

        await expectAGlobalAnnotationToExist(dialog);

        // Open canvas adjustments dialog
        await page.getByRole('button', { name: /canvas adjustments/i }).click();

        // Change a few settings
        const hideLabelsSwitch = page.getByRole('switch', { name: /hide labels/i });
        const pixelViewSwitch = page.getByRole('switch', { name: /pixel view/i });

        await hideLabelsSwitch.click();
        await pixelViewSwitch.click();

        await expect(hideLabelsSwitch).toBeChecked();
        await expect(hideLabelsSwitch).toBeChecked();

        // Close the dialog
        await page.getByRole('button', { name: /close canvas adjustments/i }).click();

        // Go to annotator page and check the canvas settings
        await page.goto(annotatorUrl);

        await page.getByRole('button', { name: /canvas adjustments/i }).click();

        await expect(page.getByRole('switch', { name: /hide labels/i })).not.toBeChecked();
        await expect(page.getByRole('switch', { name: /pixel view/i })).toBeChecked();
    });
});
