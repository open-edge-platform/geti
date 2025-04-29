// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { InferenceModel } from '../../../../src/core/annotations/services/visual-prompt-service';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { disabledFUXSettings } from '../../../fixtures/open-api/mocks';
import { annotatorUrl } from '../../../mocks/segmentation/mocks';
import { registerStoreSettings } from '../../../utils/api';
import { modelDetail, modelGroups, testResults } from './mocks';
import { activeModelPredictions, registerProjectResponses, visualPromptPredictions } from './utils';

const selectVisualPromptModel = async (page: Page) => {
    await page.getByRole('button', { name: 'Active model' }).click();
    await page.getByRole('option', { name: 'LVM: SAM' }).click();
};

const selectActiveModel = async (page: Page) => {
    await page.getByRole('button', { name: 'LVM: SAM' }).click();
    await page.getByRole('option', { name: 'Active model' }).click();
};

const expectToSeeAnnotations = async (page: Page, amount: number) => {
    const annotationsLocator = page.getByLabel('Annotator canvas').getByLabel('annotations').getByLabel('labels');

    await expect(annotationsLocator).toHaveCount(amount);
};

test.describe('Visual prompting', () => {
    test.use({ featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true } });

    test.beforeEach(async ({ page, registerApiResponse }) => {
        registerStoreSettings(registerApiResponse, disabledFUXSettings);
        registerProjectResponses(registerApiResponse);

        registerApiResponse('GetSinglePrediction', (_req, res, ctx) => {
            return res(ctx.json({ predictions: activeModelPredictions }));
        });

        // The visual prompt inference endpoint isn't documented yet, so we will use page.route
        await page.route(
            // eslint-disable-next-line max-len
            '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/pipelines/6101254defba22ca453f11d1:prompt',
            (route) => {
                route.fulfill({
                    status: 200,
                    body: JSON.stringify({
                        predictions: visualPromptPredictions,
                        created: '2024-06-21 13:57:58.524254827 +0000',
                    }),
                });
            }
        );
    });

    test('A user can switch from active learning to using a visual prompt model for inference', async ({
        annotatorPage,
        page,
    }) => {
        // Open the annotator using the active model's predictions
        await page.goto(annotatorUrl);
        await expectToSeeAnnotations(page, activeModelPredictions.length);

        await annotatorPage.selectPredictionMode();
        await expectToSeeAnnotations(page, activeModelPredictions.length);

        // Switch to the visual prompt model
        await selectVisualPromptModel(page);
        await expectToSeeAnnotations(page, visualPromptPredictions.length);

        // Submit annotations and assert that on the next media we see predictions from
        // the visual prompt model
        await annotatorPage.selectAnnotationMode();
        await annotatorPage.submit();
        await expectToSeeAnnotations(page, visualPromptPredictions.length);

        // Revert back to active model
        await annotatorPage.selectPredictionMode();
        await expectToSeeAnnotations(page, visualPromptPredictions.length);
        await selectActiveModel(page);
        await expectToSeeAnnotations(page, activeModelPredictions.length);

        // Submit annotations and assert that on the next media we see predictions from
        // the active model
        await annotatorPage.selectAnnotationMode();
        await annotatorPage.submit();
        await expectToSeeAnnotations(page, activeModelPredictions.length);
    });

    test('A user can use the Active learning configuration to switch inference models', async ({
        annotatorPage,
        page,
        aiLearningConfigurationPage,
    }) => {
        // Open the annotator using the active model's predictions
        await page.goto(annotatorUrl);
        await expectToSeeAnnotations(page, activeModelPredictions.length);

        await annotatorPage.selectPredictionMode();
        await expectToSeeAnnotations(page, activeModelPredictions.length);

        // Switch to the visual prompt model
        await aiLearningConfigurationPage.open();
        await aiLearningConfigurationPage.selectInferenceMode(InferenceModel.VISUAL_PROMPT);
        await aiLearningConfigurationPage.close();

        await expect(page.getByRole('dialog')).toBeHidden();

        await expectToSeeAnnotations(page, visualPromptPredictions.length);

        // Submit annotations and assert that on the next media we see predictions from
        // the visual prompt model
        await annotatorPage.selectAnnotationMode();
        await annotatorPage.submit();
        await expectToSeeAnnotations(page, visualPromptPredictions.length);

        // Revert back to active model
        await annotatorPage.selectPredictionMode();
        await expectToSeeAnnotations(page, visualPromptPredictions.length);
        await aiLearningConfigurationPage.open();
        await aiLearningConfigurationPage.selectInferenceMode(InferenceModel.ACTIVE_MODEL);
        await aiLearningConfigurationPage.close();

        await expect(page.getByRole('dialog')).toBeHidden();

        await expectToSeeAnnotations(page, activeModelPredictions.length);

        // Submit annotations and assert that on the next media we see predictions from
        // the active model
        await annotatorPage.selectAnnotationMode();
        await annotatorPage.submit();
        await expectToSeeAnnotations(page, activeModelPredictions.length);
    });

    test.describe('Models & tests page', () => {
        test.beforeEach(async ({ registerApiResponse }) => {
            // Mock API to return SAM model
            registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(modelGroups)));
            registerApiResponse('GetModelGroup', (_, res, ctx) => res(ctx.json(modelGroups.model_groups[0])));
            registerApiResponse('GetModelDetail', (_, res, ctx) => res(ctx.json(modelDetail)));
        });

        test('Visual prompt models are shown in the models page', async ({ page }) => {
            await page.goto(
                // eslint-disable-next-line max-len
                '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/models'
            );

            const model = page.getByLabel('SAM version');
            await expect(model).toBeVisible();

            // Check that on visual prompt models we only allow running tests
            const menu = model.getByLabel('Model action menu');
            await menu.click();
            const runTests = page.getByRole('menuitem', { name: /tests/ });
            await expect(runTests).toBeEnabled();
            await expect(page.getByRole('menuitem', { name: 'Set as active model' })).toBeDisabled();
            await expect(page.getByRole('menuitem', { name: 'Retrain' })).toBeDisabled();
            await runTests.click();

            // Check that we can run tests
            const runTestDialog = page.getByRole('dialog');
            await expect(runTestDialog).toBeVisible();
            await expect(page.getByText('Segmentation (SAM)Version')).toBeVisible();
            await page.keyboard.press('Escape');
            await expect(runTestDialog).toBeHidden();

            // Inspect visual prompt model
            await model.click();
            await expect(page.getByRole('tab', { name: 'Model variants' })).toBeVisible();
            await expect(page.getByRole('tab', { name: 'Reference dataset' })).toBeVisible();
            await expect(page.getByRole('tab', { name: 'Labels' })).toBeVisible();
            await expect(page.getByRole('tab', { name: 'Parameters' })).toBeHidden();
            await expect(page.getByRole('tab', { name: 'Model metrics' })).toBeHidden();
            await expect(page.getByText('BASELINE MODELS')).toBeVisible();

            // Check that we can download the model or run tests using it
            await page
                .getByRole('gridcell', { name: 'download model Model action' })
                .getByLabel('Model action menu')
                .click();
            await expect(page.getByRole('menuitem', { name: 'Download' })).toBeEnabled();
            await expect(page.getByRole('menuitem', { name: 'Run tests' })).toBeEnabled();

            // Check that we can run a test form the model page
            await page.getByRole('menuitem', { name: 'Run tests' }).click();
            await expect(page.getByRole('dialog')).toBeVisible();
            await expect(page.getByText('Segmentation (SAM)Version')).toBeVisible();
            await page.keyboard.press('Escape');
            await expect(page.getByRole('dialog')).toBeHidden();
        });

        test('The reference dataset shows inference results from the visual prompt model', async ({
            page,
            annotatorPage,
        }) => {
            await page.goto(
                // eslint-disable-next-line max-len
                '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/models/672d00c843da978dfb79fe98/672d00c843da978dfb79fe9a/training-datasets'
            );

            await page.getByRole('img', { name: /dummy_images/i }).click();

            // Check that we show all visual prompt predictions with the correct labels
            await expect(page.getByLabel('annotations').getByLabel('labels')).toHaveCount(0);
            await annotatorPage.selectPredictionMode();
            await expect(page.getByLabel('annotations').getByLabel('labels')).toHaveCount(
                visualPromptPredictions.length
            );

            const annotations = await page.getByLabel('annotations').getByLabel('labels').all();
            await Promise.all(annotations.map((annotation) => expect(annotation).toContainText('Card')));
        });

        test('Tests can be run using a visual prompt model', async ({ page, registerApiResponse, testsPage }) => {
            registerApiResponse('GetAllTestsInAProject', (_, res, ctx) => res(ctx.json({ test_results: testResults })));
            registerApiResponse('GetTestInAProject', (_, res, ctx) => res(ctx.json(testResults[0])));

            await page.goto(
                // eslint-disable-next-line max-len
                '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/61012cdb1d38a5e71ef3baf9/tests'
            );

            const runTestDialog = await testsPage.runTest();
            await expect(runTestDialog.getRunTestButton()).toBeEnabled();
        });
    });
});
