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
