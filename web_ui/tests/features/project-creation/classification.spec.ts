// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
