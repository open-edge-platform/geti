// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VideoPlayerPage } from '../fixtures/page-objects/annotator/video-player-page';
import { expectProjectToHaveLabels, expectProjectToHaveType } from './../features/project-creation/expect';
import { expect } from './../fixtures/base-test';
import { test } from './fixtures';
import { canAnnotateFishDataset, getFishVideoFiles, loadFishAnnotations, VideoAnnotations } from './utils';

// The amount of annotations is picked so that Geti could start training 2 times
// (each round requiring 12 annotations)
const AMOUNT_OF_ANNOTATIONS = 2 * 12;

test('Create fish detection project', async ({
    createProjectPage,
    page,
    mediaPage,
    boundingBoxTool,
    labelShortcutsPage,
    annotatorPage,
}) => {
    test.skip(canAnnotateFishDataset(), 'this test requires you to setup a local dataset');

    await page.goto('/');

    await test.step('Create project', async () => {
        const detectionLabel = 'Fish';

        await page.getByRole('button', { name: /create new/i }).click();

        const projectPage = await createProjectPage.detection('Fish detection', [detectionLabel]);

        const labels = [detectionLabel];

        await expectProjectToHaveType(projectPage, 'Detection');
        await expectProjectToHaveLabels(projectPage, labels);
    });

    await test.step('Importing media', async () => {
        await page.getByRole('link', { name: /datasets/i }).click();

        const bucket = await mediaPage.getBucket();
        await bucket.uploadFiles(getFishVideoFiles());

        await expect(page.getByText(/0 images, 5 videos/i)).toBeVisible({
            timeout: 1000 * 60 * 10,
        });
    });

    const videoPage = new VideoPlayerPage(page);
    await test.step(`Annotate ${AMOUNT_OF_ANNOTATIONS} frames`, async () => {
        await page.getByRole('button', { name: /annotate interactively/i }).click();

        // Wait for the video player to have finished loading
        await videoPage.getCurrentFrameNumber();

        await boundingBoxTool.selectTool();

        const videoAnnotations: VideoAnnotations = {};

        for (let idx = 0; idx < AMOUNT_OF_ANNOTATIONS; idx++) {
            const filename = await annotatorPage.selectedMediaFilename();
            loadFishAnnotations(filename, videoAnnotations);

            const frameNumber = await videoPage.getCurrentFrameNumber();
            const annotations = videoAnnotations[filename][frameNumber];

            await page.keyboard.press('Control+a');
            await page.keyboard.press('Delete');

            if (annotations.length === 0) {
                await (await labelShortcutsPage.getPinnedLabelLocator('No object')).click();
            }

            for (const annotation of annotations) {
                if (annotation.labels.some((label) => label === 'Diver')) {
                    continue;
                }

                await boundingBoxTool.drawBoundingBox(annotation.shape);

                // Deselect the annotation so that when we draw the new annotation we
                // don't accidentally press on the "Edit label" button
                await page.keyboard.press('Control+d');
            }

            const url = page.url();
            await annotatorPage.submit();
            await expect(page).not.toHaveURL(url);
        }
    });
});
