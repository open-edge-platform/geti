// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VideoPlayerPage } from '../fixtures/page-objects/annotator/video-player-page';
import { expectProjectToHaveLabels, expectProjectToHaveType } from './../features/project-creation/expect';
import { expect } from './../fixtures/base-test';
import { test } from './fixtures';
import { canAnnotateFishDataset, getFishVideoFiles, loadFishAnnotations, VideoAnnotations } from './utils';

// The amount of annotations is picked so that Geti could start training 2 times (each round requiring 12 annotations)
const AMOUNT_OF_ANNOTATIONS = 2 * 12;

test('Create fish detection classification project', async ({
    createProjectPage,
    page,
    mediaPage,
    boundingBoxTool,
    labelShortcutsPage,
    annotatorPage,
}) => {
    test.skip(canAnnotateFishDataset(), 'this test requires you to setup a local dataset');

    await page.goto('/');

    const detectionLabel = 'Fish';
    const classificationLabels: Record<string, string[]> = {
        Fish: ['Tuna', 'SiameseFish', 'GoldFish', 'RedYellowFish', 'YellowFish', 'BlueFish', 'ClownFish'],
    };
    const labels = [
        detectionLabel,
        ...Object.keys(classificationLabels).flatMap((group) => classificationLabels[group]),
    ];

    await test.step('Create project', async () => {
        await page.getByRole('button', { name: /create new/i }).click();

        const projectPage = await createProjectPage.detectionClassification(
            'Fish detection classification',
            detectionLabel,
            classificationLabels
        );

        await expectProjectToHaveType(projectPage, 'Detection→Classification');
        await expectProjectToHaveLabels(projectPage, labels);
    });

    await test.step('importing media', async () => {
        await page.getByRole('link', { name: /datasets/i }).click();

        const bucket = await mediaPage.getBucket();

        const files = getFishVideoFiles();
        await bucket.uploadFiles(files);

        await expect(page.getByText(/0 images, 5 videos/i)).toBeVisible({
            timeout: 1000 * 60 * 10,
        });
    });

    const videoPage = new VideoPlayerPage(page);
    await test.step(`Annotate ${AMOUNT_OF_ANNOTATIONS} frames`, async () => {
        await page.getByRole('button', { name: /annotate interactively/i }).click();

        // Wait for the video player to have finished loading
        expect(await videoPage.getCurrentFrameNumber()).not.toBeNaN();

        await boundingBoxTool.selectTool();

        // Pin label shortcuts for easy access
        await labelShortcutsPage.openLabelShortcutsMenu();
        await labelShortcutsPage.pinLabel('RedYellowFish');
        await labelShortcutsPage.pinLabel('BlueFish');
        await labelShortcutsPage.pinLabel('YellowFish');
        await labelShortcutsPage.pinLabel('ClownFish');
        await labelShortcutsPage.closeLabelShortcutsMenu();

        const videoAnnotations: VideoAnnotations = {};

        let lastLabel = '';
        for (let idx = 0; idx < AMOUNT_OF_ANNOTATIONS; idx++) {
            const filename = await annotatorPage.selectedMediaFilename();
            loadFishAnnotations(filename, videoAnnotations);

            const frameNumber = await videoPage.getCurrentFrameNumber();
            const annotations = videoAnnotations[filename][frameNumber];
            await page.keyboard.press('Control+a');
            await page.keyboard.press('Delete');

            if (annotations.length === 0) {
                (await labelShortcutsPage.getPinnedLabelLocator('No object')).click();
            }

            for (const annotation of annotations) {
                if (annotation.labels.some((label) => label === 'Diver')) {
                    continue;
                }

                await boundingBoxTool.drawBoundingBox(annotation.shape);

                const currentLabel = annotation.labels.find((label) => label !== 'Fish') ?? '';
                if (lastLabel !== currentLabel) {
                    const label = await labelShortcutsPage.getPinnedLabelLocator(currentLabel, true);
                    await label.click();
                }

                lastLabel = currentLabel;

                // Deselect the annotation so that when we draw the new annotation
                // we don't press on the "Edit label" button
                await page.keyboard.press('Control+d');
            }

            const url = page.url();
            await annotatorPage.submit();
            await expect(page).not.toHaveURL(url);
        }
    });
    console.info('finished');
});
