// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, test as testBase } from '@playwright/test';

import { BoundingBoxToolPage } from '../annotator/bounding-box-tool-page';
import { AnnotatorPage } from '../datasets/annotator-page';
import { DatasetPage } from '../datasets/dataset-page';
import { ModelsPage } from '../models/models-page';
import { ProjectPage } from '../projects/project-page';

interface Fixtures {
    projectPage: ProjectPage;
    datasetPage: DatasetPage;
    annotatorPage: AnnotatorPage;
    boundingBoxTool: BoundingBoxToolPage;
    modelsPage: ModelsPage;
}

const test = testBase.extend<Fixtures>({
    projectPage: async ({ page }, use) => {
        const projectPage = new ProjectPage(page);

        await use(projectPage);
    },
    datasetPage: async ({ page }, use) => {
        const datasetPage = new DatasetPage(page);
        await use(datasetPage);
    },
    annotatorPage: async ({ page }, use) => {
        const annotatorPage = new AnnotatorPage(page);
        await use(annotatorPage);
    },
    boundingBoxTool: async ({ page }, use) => {
        const boundingBoxTool = new BoundingBoxToolPage(page);
        await use(boundingBoxTool);
    },
    modelsPage: async ({ page }, use) => {
        const modelsPage = new ModelsPage(page);

        await use(modelsPage);
    },
});

export { test, expect };
