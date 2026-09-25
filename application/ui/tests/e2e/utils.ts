// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import fs from 'fs';
import { readFile } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

import type { Page } from '@playwright/test';

import type { BoundingBoxToolPage } from '../annotator/bounding-box-tool-page';
import type { AnnotatorPage } from '../datasets/annotator-page';
import { ANNOTATIONS_TO_DRAW_PER_ASSET } from './assets-annotations';
import { expectMediaItemToChange } from './expects';
import { expect } from './fixtures';

const getDirname = () => {
    const filename = fileURLToPath(import.meta.url);

    return path.dirname(filename);
};

export const getFilesToUpload = (relativePathToAssetDirectory: string) => {
    const dirname = getDirname();

    const files = fs.readdirSync(path.join(dirname, relativePathToAssetDirectory));
    return files.map((file) => path.join(dirname, relativePathToAssetDirectory, file));
};

export const getAssetName = (filePath: string) => path.parse(filePath).name;

export const isZipFile = async (filePath: string) => {
    const content = await readFile(filePath);

    return content.subarray(0, 2).toString('latin1') === 'PK';
};

/** Draws the boxes listed in `ANNOTATIONS_TO_DRAW_PER_ASSET` on every media item, starting from the open one. */
export const annotateMediaItems = async ({
    page,
    annotatorPage,
    boundingBoxTool,
    count,
    timeout,
}: {
    page: Page;
    annotatorPage: AnnotatorPage;
    boundingBoxTool: BoundingBoxToolPage;
    count: number;
    timeout: number;
}) => {
    let prevImageName: string | null = null;

    for (let i = 0; i < count; i++) {
        await expect(annotatorPage.getMediaCanvasLoading()).toBeHidden({ timeout });

        await expectMediaItemToChange(annotatorPage, prevImageName, timeout);

        const imageName = (await annotatorPage.getSelectedMediaItem().getAttribute('alt')) as string;

        prevImageName = imageName;

        const annotations = ANNOTATIONS_TO_DRAW_PER_ASSET[imageName];

        for (const annotation of annotations) {
            await boundingBoxTool.selectTool();

            await boundingBoxTool.drawBoundingBox(annotation.shape);

            const label = page.getByLabel('Labels').getByRole('button', { name: `Label ${annotation.label}` });
            const isLabelAlreadySelected = (await label.getAttribute('aria-pressed')) === 'true';

            if (!isLabelAlreadySelected) {
                await label.click();
            }
        }

        const saveResponse = await annotatorPage.submitAndWaitForSave();
        expect(saveResponse.ok()).toBeTruthy();
    }
};
