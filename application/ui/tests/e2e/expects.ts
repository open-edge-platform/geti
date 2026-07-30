// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotatorPage } from '../datasets/annotator-page';
import { expect } from './fixtures';

export const expectMediaItemToChange = async (
    annotatorPage: AnnotatorPage,
    prevImageName: string | null,
    timeout: number
) => {
    await expect(async () => {
        if (prevImageName === null) {
            return true;
        }

        const selectedMediaItem = annotatorPage.getSelectedMediaItem();

        await expect(selectedMediaItem).not.toHaveAttribute('alt', prevImageName);
    }).toPass({ timeout });
};
