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
import { testWithOpenApi as test } from './fixtures';

test.describe('Anomaly project creation', () => {
    test.describe('With disabled anomaly reduction', () => {
        test.beforeEach(({ registerFeatureFlags }) => {
            registerFeatureFlags({ FEATURE_FLAG_ANOMALY_REDUCTION: false });
        });

        test('Create anomaly classification project', async ({ createProjectPage }) => {
            const projectPage = await createProjectPage.anomalyClassification(
                'Playwright Cat & Dog anomaly classification'
            );

            await expectProjectToHaveType(projectPage, 'Anomaly classification');
            await expectProjectToHaveLabels(projectPage, ['Normal', 'Anomalous']);
        });

        test('Create anomaly detection project', async ({ createProjectPage }) => {
            const projectPage = await createProjectPage.anomalyDetection('Playwright Cat & Dog anomaly detection');

            await expectProjectToHaveType(projectPage, 'Anomaly detection');
            await expectProjectToHaveLabels(projectPage, ['Normal', 'Anomalous']);
        });

        test('Create anomaly segmentation project', async ({ createProjectPage }) => {
            const projectPage = await createProjectPage.anomalySegmentation(
                'Playwright Cat & Dog anomaly segmentation'
            );

            await expectProjectToHaveType(projectPage, 'Anomaly segmentation');
            await expectProjectToHaveLabels(projectPage, ['Normal', 'Anomalous']);
        });
    });

    test.describe('With enabled anomaly reduction', () => {
        test.beforeEach(({ registerFeatureFlags }) => {
            registerFeatureFlags({ FEATURE_FLAG_ANOMALY_REDUCTION: true });
        });

        test('Create anomaly detection project', async ({ createProjectPage }) => {
            const projectPage = await createProjectPage.anomalyDetection('Playwright Cat & Dog anomaly detection');

            await expectProjectToHaveType(projectPage, 'Anomaly detection');
            await expectProjectToHaveLabels(projectPage, ['Normal', 'Anomalous']);
        });
    });
});
