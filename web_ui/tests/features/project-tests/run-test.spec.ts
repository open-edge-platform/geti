// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import cloneDeep from 'lodash/cloneDeep';

import { TASK_TYPE } from '../../../src/core/projects/dtos/task.interface';
import { OpenApiResponseBody } from '../../../src/core/server/types';
import { test as baseTest, expect } from '../../fixtures/base-test';
import { extendWithOpenApi } from '../../fixtures/open-api';
import { TestConfiguration } from '../../fixtures/page-objects/run-test-dialog-page';
import { project } from '../../mocks/classification/mocks';
import { project as detectionClassificationProject } from './../../mocks/detection-classification/mocks';
import { expectTestConfiguration } from './expect';

const PROJECT_TESTS =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/63283aedc80c9c686fd3b1e6/tests';
const test = extendWithOpenApi(baseTest);

test.beforeEach(({ registerApiResponse, openApi }) => {
    registerApiResponse('GetModelGroups', (_, res, ctx) => {
        const { mock, status } = openApi.mockResponseForOperation('GetModelGroups') as {
            mock: OpenApiResponseBody<'GetModelGroups'>;
            status: number;
        };

        const task_id = (project.pipeline?.tasks ?? []).find((task) => task.task_type !== 'dataset')?.id;
        const model_groups = mock?.model_groups?.map((modelGroup) => {
            return { ...modelGroup, task_id };
        });

        return res(ctx.status(status), ctx.json({ model_groups }));
    });

    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        return res(ctx.json(cloneDeep(project)));
    });
});

test('From testing screen', async ({ page, testsPage }) => {
    await page.goto(PROJECT_TESTS);

    const runTestDialogPage = await testsPage.runTest();

    const configuration: TestConfiguration = {
        testName: 'T1',
        dataset: 'dataset',
        optimization: 'model OpenVINO',
        version: 'Version 2',
        model: 'U-Net',
    };
    await runTestDialogPage.configureTest(configuration);

    await expectTestConfiguration(page, configuration);

    await runTestDialogPage.runTest();

    await expect(page.getByText(/test has started/i)).toBeVisible();
});

test('Lets the user choose a metric for anomaly localization projects', async ({
    page,
    testsPage,
    registerApiResponse,
}) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        const anomalyDetectionProject = cloneDeep(project);
        anomalyDetectionProject.pipeline.tasks[1].task_type = TASK_TYPE.ANOMALY_DETECTION;
        return res(ctx.json(anomalyDetectionProject));
    });

    await page.goto(PROJECT_TESTS);
    const runTestDialogPage = await testsPage.runTest();

    const configuration: TestConfiguration = {
        testName: 'T1',
        dataset: 'dataset',
        optimization: 'model OpenVINO',
        version: 'Version 2',
        model: 'U-Net',
        metric: 'Object score',
    };
    await runTestDialogPage.configureTest(configuration);
    await expectTestConfiguration(page, configuration);

    await runTestDialogPage.runTest();
    await expect(page.getByText(/test has started/i)).toBeVisible();
});

test('Selecting a task to test in a task chain project', async ({ page, testsPage, registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        return res(ctx.json(cloneDeep(detectionClassificationProject)));
    });

    await page.goto(PROJECT_TESTS);
    const runTestDialogPage = await testsPage.runTest();

    await test.step('Can not start a test for a task without models', async () => {
        await runTestDialogPage.configureTest({ task: 'Detection' });

        expect(await runTestDialogPage.getAlertMessage()).toEqual(
            'No trained models. Go to the annotation tool and annotate images/frames.'
        );
    });

    const configuration: TestConfiguration = {
        testName: 'T1',
        task: 'Classification',
        dataset: 'dataset',
        optimization: 'model OpenVINO',
        version: 'Version 2',
        model: 'U-Net',
    };

    await runTestDialogPage.configureTest(configuration);
    await expectTestConfiguration(page, configuration);

    await runTestDialogPage.runTest();
});

test('Disabled when no models exist', async ({ page, registerApiResponse }) => {
    registerApiResponse('GetModelGroups', async (_, res, ctx) => {
        return res(ctx.status(200), ctx.json({ model_groups: [] }));
    });

    await page.goto(PROJECT_TESTS);

    await expect(page.getByRole('button', { name: /run test/i })).toBeDisabled();
});

test('Disabled when test name is empty', async ({ page, registerApiResponse, testsPage }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        return res(ctx.json(cloneDeep(detectionClassificationProject)));
    });

    await page.goto(PROJECT_TESTS);

    const runTestDialogPage = await testsPage.runTest();

    const configuration: TestConfiguration = {
        testName: 'T1',
        task: 'Classification',
        dataset: 'dataset',
        optimization: 'model OpenVINO',
        version: 'Version 2',
        model: 'U-Net',
    };

    await runTestDialogPage.configureTest(configuration);
    await expectTestConfiguration(page, configuration);

    await runTestDialogPage.inputTestName('');

    await expect(runTestDialogPage.getRunTestButton()).toBeDisabled();
    await expect(page.getByText('Test name cannot be empty')).toBeVisible();
});

test('Disabled when such test name already exists', async ({ openApi, page, registerApiResponse, testsPage }) => {
    const existingName = 'T1';

    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        return res(ctx.json(cloneDeep(detectionClassificationProject)));
    });

    registerApiResponse('GetAllTestsInAProject', (_, res, ctx) => {
        const { mock, status } = openApi.mockResponseForOperation('GetAllTestsInAProject') as {
            status: number;
            mock: OpenApiResponseBody<'GetAllTestsInAProject'>;
        };

        // Make sure a test exists with our given dataset and model
        const test_results = cloneDeep(mock.test_results);
        test_results[0].datasets_info[0].id = '63283aedc80c9c686fd3b1e8';
        test_results[0].model_info.id = '60dc3b8b3fc7834f46ea90af';
        test_results[0].model_info.group_id = '60dc3b8b3fc7834f46ea90d5';
        test_results[0].model_info.version = 2;
        test_results[0].name = existingName;

        return res(ctx.status(status), ctx.json({ test_results }));
    });

    await page.goto(PROJECT_TESTS);

    const runTestDialogPage = await testsPage.runTest();

    const configuration: TestConfiguration = {
        testName: 'T2',
        task: 'Classification',
        dataset: 'dataset',
        optimization: 'model OpenVINO',
        version: 'Version 2',
        model: 'U-Net',
    };

    await runTestDialogPage.configureTest(configuration);
    await expectTestConfiguration(page, configuration);

    await runTestDialogPage.inputTestName(existingName);

    await expect(runTestDialogPage.getRunTestButton()).toBeDisabled();
    await expect(page.getByText('Test name must be unique')).toBeVisible();
});

test('Showing warning messages', async ({ page, registerApiResponse, openApi, testsPage }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        const datasets = [
            ...(project.datasets ?? []),
            {
                creation_time: '2022-09-19T09:48:29.259000+00:00',
                id: '63283aedc80c9c686fd3b1e8',
                name: 'Testing set 1',
                use_for_training: false,
            },
        ];

        return res(ctx.json({ ...project, datasets }));
    });

    registerApiResponse('GetAllTestsInAProject', (_, res, ctx) => {
        const { mock, status } = openApi.mockResponseForOperation('GetAllTestsInAProject') as {
            status: number;
            mock: OpenApiResponseBody<'GetAllTestsInAProject'>;
        };

        // Make sure a test exists with our given dataset and model
        const test_results = cloneDeep(mock.test_results);
        test_results[0].datasets_info[0].id = '63283aedc80c9c686fd3b1e8';
        test_results[0].model_info.id = '60dc3b8b3fc7834f46ea90af';
        test_results[0].model_info.group_id = '60dc3b8b3fc7834f46ea90d5';
        test_results[0].model_info.version = 2;

        return res(ctx.status(status), ctx.json({ test_results }));
    });

    await page.goto(PROJECT_TESTS);
    const runTestDialogPage = await testsPage.runTest();

    const configuration: TestConfiguration = {
        testName: 'T1',
        dataset: 'dataset',
        optimization: 'model OpenVINO',
        version: 'Version 2',
        model: 'U-Net',
    };

    await runTestDialogPage.configureTest(configuration);

    await expectTestConfiguration(page, configuration);

    expect(await runTestDialogPage.getAlertMessage()).toEqual(
        'This is your training set, it is not recommended to use as a testing set. Create testing set.'
    );

    await runTestDialogPage.configureTest({ dataset: 'Testing set 1', version: 'Version 2' });

    expect(await runTestDialogPage.getAlertMessage()).toEqual(
        'This testing set has been tested with this configuration.'
    );
});

// NOTE: in this case we should inform the user about the model version
// (or do extra check on model version),
// and inform them of the date of this test, possibly with a link to the test
test('Testing with an invalid dataset', async ({ page, registerApiResponse, openApi, testsPage }) => {
    const errorResponse = {
        error_code: 'dataset_has_no_annotations',
        http_status: 409,
        message: `Dataset '${project.datasets[0].name}' has no annotations.`,
    };

    registerApiResponse('GetAllTestsInAProject', (_, res, ctx) => {
        const { mock, status } = openApi.mockResponseForOperation('GetAllTestsInAProject') as {
            status: number;
            mock: OpenApiResponseBody<'GetAllTestsInAProject'>;
        };

        const test_results = cloneDeep(mock.test_results);
        test_results[0].job_info.id = '62e2b0deddb0eebbcb1c1a0a';
        test_results[0].job_info.status = 'ERROR';

        return res(ctx.status(status), ctx.json({ test_results }));
    });

    registerApiResponse('TriggerModelTestJob', (_, res, ctx) => {
        return res(ctx.status(errorResponse.http_status), ctx.json(errorResponse));
    });

    await page.goto(PROJECT_TESTS);

    const runTestDialogPage = await testsPage.runTest();

    const configuration: TestConfiguration = {
        testName: 'T1',
        dataset: 'dataset',
        optimization: 'model OpenVINO',
        version: 'Version 2',
        model: 'U-Net',
    };
    await runTestDialogPage.configureTest(configuration);
    await expectTestConfiguration(page, configuration);

    await runTestDialogPage.runTest();

    await expect(page.getByText(errorResponse.message, { exact: false })).toBeVisible();
});
