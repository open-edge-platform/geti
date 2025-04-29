// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import cloneDeep from 'lodash/cloneDeep';

import { OpenApiResponseBody } from '../../../src/core/server/types';
import { test as baseTest, expect } from '../../fixtures/base-test';
import { extendWithOpenApi } from '../../fixtures/open-api';
import { switchCallsAfter } from '../../utils/api';
import { expectToBeOnTheTestPage } from './expect';

const PROJECT_TESTS =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/63283aedc80c9c686fd3b1e6/tests';

const switchAfterOneCall = switchCallsAfter(1);

const test = extendWithOpenApi(baseTest).extend<{ testsResponse: OpenApiResponseBody<'GetAllTestsInAProject'> }>({
    testsResponse: async ({ openApi }, use) => {
        const { mock } = openApi.mockResponseForOperation('GetAllTestsInAProject') as {
            mock: OpenApiResponseBody<'GetAllTestsInAProject'>;
            status: number;
        };

        const testResults = cloneDeep(mock.test_results).map((testResult, index) => {
            return { ...testResult, name: `T${index + 1}`, id: index.toString() };
        });

        await use({ ...mock, test_results: testResults });
    },
});

test.describe('Project Tests', () => {
    test('Two tabs are visible: Tests and Live prediction', async ({ page }) => {
        await page.goto(PROJECT_TESTS);

        await expect(page.getByRole('tab', { name: 'Tests' })).toBeVisible();
        await expect(page.getByRole('tab', { name: 'Live prediction' })).toBeVisible();
    });

    test('Tabs are url aware and the other way around', async ({ page }) => {
        await page.goto(PROJECT_TESTS);

        const testsTab = page.getByRole('tab', { name: 'Tests' });
        const livePredictionTab = page.getByRole('tab', { name: 'Live prediction' });

        await expect(testsTab).toHaveAttribute('aria-selected', 'true');
        await expect(livePredictionTab).toHaveAttribute('aria-selected', 'false');

        await livePredictionTab.click();

        await expect(page).toHaveURL(new RegExp(`${PROJECT_TESTS}/live-prediction`));
        await expect(livePredictionTab).toHaveAttribute('aria-selected', 'true');
        await expect(testsTab).toHaveAttribute('aria-selected', 'false');
    });

    test('Open a test after it finishes', async ({ page, testsPage, registerApiResponse, testsResponse }) => {
        registerApiResponse(
            'GetAllTestsInAProject',
            switchAfterOneCall([
                async (_, res, ctx) => res(ctx.json(testsResponse)),
                async (_, res, ctx) => {
                    const completedTestResults = testsResponse.test_results.map((testResult, index) => {
                        if (index === 0) {
                            return {
                                ...testResult,
                                job_info: { ...testResult.job_info, status: 'DONE' },
                                scores: [
                                    {
                                        name: 'F-measure',
                                        value: 0.7804878048780486,
                                        label_id: null,
                                    },
                                ],
                            };
                        }

                        return testResult;
                    });

                    return res(ctx.json({ test_results: completedTestResults }));
                },
            ])
        );
        await page.goto(PROJECT_TESTS);

        await testsPage.waitForTestToFinish('T1');
        await testsPage.gotoTest('T1');

        await expectToBeOnTheTestPage(page);
    });

    test('Removing a test', async ({ page, testsPage, registerApiResponse, testsResponse }) => {
        registerApiResponse(
            'GetAllTestsInAProject',
            switchAfterOneCall([
                async (_, res, ctx) => {
                    return res(ctx.json(testsResponse));
                },
                async (_, res, ctx) => {
                    const completedTestResults = testsResponse.test_results.filter((result) => result.id !== '2');

                    return res(ctx.json({ test_results: completedTestResults }));
                },
            ])
        );

        await page.goto(PROJECT_TESTS);

        // 4 + header
        await expect(page.getByRole('row')).toHaveCount(5);

        await testsPage.deleteTest('T2');

        await expect(page.getByRole('row')).toHaveCount(4);
    });
});
