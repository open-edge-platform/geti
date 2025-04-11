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

testWithOpenApi.skip('Create detection -> classification project', async ({ page, createProjectPage }) => {
    const detectionLabel = 'Card';
    const classificationLabels: Record<string, string[]> = {
        Suit: ['Hearts', 'Diamonds', 'Spades', 'Clubs'],
        Value: ['7', '8', '9', '10', 'J', 'Q', 'K', 'A'],
    };
    const projectPage = await createProjectPage.detectionClassification(
        'Playwright card detection suit classification',
        detectionLabel,
        classificationLabels
    );

    const labels = [
        detectionLabel,
        ...Object.keys(classificationLabels).flatMap((group) => classificationLabels[group]),
    ];

    await expectProjectToHaveType(projectPage, 'Detection→Classification');
    await expectProjectToHaveLabels(projectPage, labels);
    await expectProjectHasHierarchicalLabels(page, classificationLabels);
});

testWithOpenApi('Create detection -> segmentation project', async ({ createProjectPage }) => {
    const detectionLabel = 'Car';
    const segmentationLabels = ['Tire', 'Mirror'];

    const projectPage = await createProjectPage.detectionSegmentation(
        'Playwright car detection segmentation',
        detectionLabel,
        segmentationLabels
    );

    const labels = [detectionLabel, ...segmentationLabels];

    await expectProjectToHaveType(projectPage, 'Detection→Segmentation');
    await expectProjectToHaveLabels(projectPage, labels);
});
