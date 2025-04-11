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

import { expect } from '@playwright/test';

import { ProjectModelsPage } from '../../fixtures/page-objects/models-page';
import { TestConfiguration } from '../../fixtures/page-objects/run-test-dialog-page';
import { expectTestConfiguration } from './../project-tests/expect';
import { testWithModels } from './fixtures';
import { getModelDetail } from './models.mocks';

const MODELS_URL =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/63283aedc80c9c686fd3b1e6/models';

interface RunTestFixtures {
    modelsPage: ProjectModelsPage;
}

const test = testWithModels.extend<RunTestFixtures>({
    modelsPage: async ({ registerApiResponse, modelsPage }, use) => {
        let hasBeenCalled = false;
        registerApiResponse('TriggerModelTestJob', (_, res, ctx) => {
            hasBeenCalled = true;

            return res(ctx.status(201));
        });

        await use(modelsPage);

        expect(hasBeenCalled).toEqual(true);
    },
});

test('Run tests from models index page', async ({ page, modelsPage }) => {
    await page.goto(MODELS_URL);
    const runTestDialogPage = await modelsPage.openTestDialog('EfficientNet-B0', '2');

    const configuration: TestConfiguration = {
        optimization: 'OpenVINO',
        dataset: 'dataset',
    };
    await runTestDialogPage.configureTest(configuration);

    await expectTestConfiguration(page, { ...configuration, version: 'Version 2', model: 'EfficientNet-B0' });

    await runTestDialogPage.runTest();
    await modelsPage.seeTestProgress();
});

test('Run tests from model page', async ({ page, modelsPage }) => {
    await page.goto(MODELS_URL);

    const modelPage = await modelsPage.goToModel('EfficientNet-B0', '2');

    const runTestDialogPage = await modelPage.openTestDialog('EfficientNet-B0 OpenVINO');

    const configuration: TestConfiguration = { dataset: 'dataset' };
    await runTestDialogPage.configureTest(configuration);
    await expectTestConfiguration(page, {
        ...configuration,
        optimization: 'OpenVINO',
        version: 'Version 2',
        model: getModelDetail.name,
    });

    await runTestDialogPage.runTest();
    await modelsPage.seeTestProgress();
});
