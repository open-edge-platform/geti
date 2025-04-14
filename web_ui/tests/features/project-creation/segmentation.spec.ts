// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expectProjectToHaveLabels, expectProjectToHaveType } from './expect';
import { testWithOpenApi } from './fixtures';

testWithOpenApi('Create segmentation project', async ({ createProjectPage }) => {
    const labels = ['Card'];
    const projectPage = await createProjectPage.segmentation('Playwright card segmentation', labels);

    await expectProjectToHaveType(projectPage, 'Segmentation');
    await expectProjectToHaveLabels(projectPage, labels);
});

testWithOpenApi('Create instance segmentation project', async ({ createProjectPage }) => {
    const labels = ['Card'];
    const projectPage = await createProjectPage.instanceSegmentation('Playwright card instance segmentation', labels);

    await expectProjectToHaveType(projectPage, 'Instance segmentation');
    await expectProjectToHaveLabels(projectPage, labels);
});
