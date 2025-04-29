// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expectProjectHasHierarchicalLabels, expectProjectToHaveLabels, expectProjectToHaveType } from './expect';
import { testWithOpenApi } from './fixtures';

testWithOpenApi('Create classification project', async ({ createProjectPage }) => {
    const labels = ['Cat', 'Dog'];
    const projectPage = await createProjectPage.classification('Playwright Cat & Dog classification', labels);

    await expectProjectToHaveType(projectPage, 'Classification');
    await expectProjectToHaveLabels(projectPage, labels);
});

testWithOpenApi('Create multi label classification project', async ({ createProjectPage }) => {
    const labels = ['Cat', 'Dog'];
    const projectPage = await createProjectPage.classificationMultiLabel('Playwright Cat & Dog classification', labels);

    await expectProjectToHaveType(projectPage, 'Classification');
    await expectProjectToHaveLabels(projectPage, labels);
});

testWithOpenApi('Create hierarchical classification project', async ({ createProjectPage, page }) => {
    const labels: Record<string, string[]> = {
        Suit: ['Hearts', 'Diamonds', 'Spades', 'Clubs'],
        Value: ['7', '8', '9', '10', 'J', 'Q', 'K', 'A'],
    };
    const projectPage = await createProjectPage.classificationHierarchical(
        'Playwright Cat & Dog classification',
        labels
    );

    await expectProjectToHaveType(projectPage, 'Classification');
    await expectProjectToHaveLabels(
        projectPage,
        Object.keys(labels).flatMap((group) => labels[group])
    );

    await expectProjectHasHierarchicalLabels(page, labels);
});
