// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expectProjectToHaveLabels, expectProjectToHaveType } from './expect';
import { testWithOpenApi } from './fixtures';

testWithOpenApi('Create detection project', async ({ createProjectPage }) => {
    const labels = ['Card'];
    const projectPage = await createProjectPage.detection('Playwright card detection', labels);

    await expectProjectToHaveType(projectPage, 'Detection');
    await expectProjectToHaveLabels(projectPage, labels);
});

testWithOpenApi('Create oriented detection project', async ({ createProjectPage }) => {
    const labels = ['Card'];
    const projectPage = await createProjectPage.orientedDetection('Playwright card oriented detection', labels);

    await expectProjectToHaveType(projectPage, 'Detection oriented');
    await expectProjectToHaveLabels(projectPage, labels);
});
