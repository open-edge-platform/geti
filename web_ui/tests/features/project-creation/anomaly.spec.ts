// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
