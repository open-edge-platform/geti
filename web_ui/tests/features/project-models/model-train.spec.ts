// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';
import { orderBy } from 'lodash-es';

import { ModelConfigurationOption } from '../../../src/pages/project-details/components/project-models/legacy-train-model-dialog/model-templates-selection/utils';
import {
    getMockedProjectStatusDTO,
    getMockedProjectStatusTask,
} from '../../../src/test-utils/mocked-items-factory/mocked-project';
import { supportedAlgorithms } from '../../fixtures/open-api/mocks';
import { ProjectModelsPage } from '../../fixtures/page-objects/models-page';
import { project as chainProject } from '../../mocks/detection-segmentation/mocks';
import { testWithModels } from './fixtures';
import { segmentationConfigurationMock } from './mocks';
import { getModelGroups } from './models.mocks';

const CLASSIFICATION_MODELS_URL =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/63283aedc80c9c686fd3b1e6/models';
const CHAIN_TASK_MODELS_PAGE_URL =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/635fce72fc03e87df9becd13/models';

interface ModelTrainFixtures {
    modelsPage: ProjectModelsPage;
}

const test = testWithModels.extend<ModelTrainFixtures>({
    modelsPage: async ({ modelsPage, registerApiResponse }, use) => {
        let trainHasBeenCalled = false;
        registerApiResponse('TrainModel', (_, res, ctx) => {
            trainHasBeenCalled = true;

            return res(ctx.status(201));
        });

        await use(modelsPage);

        expect(trainHasBeenCalled).toBe(true);
    },
});

const expectTaskSelectorVisible = async (page: Page) => {
    await expect(page.getByRole('button', { name: /select domain task/i })).toBeVisible();
};

test.describe('Test model train dialog pipeline', () => {
    test('Train model for classification', async ({ modelsPage, page, registerApiResponse }) => {
        registerApiResponse('GetProjectStatus', (_, res, ctx) => {
            return res(
                // @ts-expect-error Issue ie openapi types
                ctx.json(
                    getMockedProjectStatusDTO({
                        tasks: [getMockedProjectStatusTask({ id: '6101254defba22ca453f11d1', ready_to_train: true })],
                    })
                )
            );
        });
        await page.goto(CLASSIFICATION_MODELS_URL);

        const trainModelDialog = await modelsPage.openTrainDialog();

        await trainModelDialog.selectModelTemplate('U-Net');
        await trainModelDialog.train();
    });

    test('Train model for the task chain', async ({ modelsPage, page, registerApiResponse }) => {
        registerApiResponse('GetProjectStatus', (_, res, ctx) => {
            return res(
                // @ts-expect-error Issue ie openapi types
                ctx.json(
                    getMockedProjectStatusDTO({
                        tasks: [
                            getMockedProjectStatusTask({ id: '635fce72fc03e87df9becd10', ready_to_train: true }),
                            getMockedProjectStatusTask({ id: '635fce72fc03e87df9becd12', ready_to_train: true }),
                        ],
                    })
                )
            );
        });

        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.status(200), ctx.json(chainProject));
        });

        registerApiResponse('GetModelGroups', (_, res, ctx) => {
            const tasks = (chainProject.pipeline?.tasks ?? []).filter(
                ({ task_type }) => !['dataset', 'crop'].includes(task_type)
            );

            const algorithmsForFirstTask =
                supportedAlgorithms.supported_algorithms?.filter(
                    ({ task_type }) => task_type === tasks[0]?.task_type
                ) ?? [];

            const algorithmsForSecondTask =
                supportedAlgorithms.supported_algorithms?.filter(
                    ({ task_type }) => task_type === tasks[1]?.task_type
                ) ?? [];

            const sortedAlgorithmsForFirstTask = orderBy(algorithmsForFirstTask, 'gigaflops', 'asc');
            const sortedAlgorithmsForSecondTask = orderBy(algorithmsForSecondTask, 'gigaflops', 'asc');

            const modelGroupsForFirstTask =
                getModelGroups.model_groups?.map((modelGroup) => {
                    return {
                        ...modelGroup,
                        id: 'model-group-1-id',
                        task_id: tasks[0]?.id,
                        model_template_id: sortedAlgorithmsForFirstTask[0]?.model_template_id,
                    };
                }) ?? [];

            const modelGroupsForSecondTask =
                getModelGroups.model_groups?.map((modelGroup) => {
                    return {
                        ...modelGroup,
                        id: 'model-group-2-id',
                        task_id: tasks[1]?.id,
                        model_template_id: sortedAlgorithmsForSecondTask[0]?.model_template_id,
                    };
                }) ?? [];

            return res(
                ctx.status(200),
                ctx.json({ model_groups: [...modelGroupsForFirstTask, ...modelGroupsForSecondTask] })
            );
        });

        await page.goto(CHAIN_TASK_MODELS_PAGE_URL);

        const trainModelDialog = await modelsPage.openTrainDialog();

        await expectTaskSelectorVisible(page);
        await trainModelDialog.selectTaskType('Segmentation');

        await trainModelDialog.selectModelAlgorithm('U-Net');
        await trainModelDialog.selectModelConfigurationOption(ModelConfigurationOption.MANUAL_CONFIGURATION);

        await trainModelDialog.nextStep();

        await trainModelDialog.previousStep();
        const activeModel = page.getByTestId('model-templates-list-id').getByLabel('Selected card');

        await expect(activeModel.getByRole('radio', { name: /U-Net/i })).toBeVisible();
        await expect(page.getByRole('radio', { name: ModelConfigurationOption.MANUAL_CONFIGURATION })).toBeChecked();

        await trainModelDialog.selectTaskType('Detection');
        await trainModelDialog.selectModelTemplate('ATSS');
        const activeTemplateDetection = page.getByTestId('model-templates-list-id').getByLabel('Selected card');

        await expect(activeTemplateDetection.getByText('ATSS')).toBeVisible();

        await trainModelDialog.selectTaskType('Segmentation');
        await trainModelDialog.selectModelConfigurationOption(ModelConfigurationOption.MANUAL_CONFIGURATION);

        await trainModelDialog.selectModelAlgorithm('U-Net');
        await trainModelDialog.nextStep();

        await trainModelDialog.train();
    });

    test.describe('Configure parameters', () => {
        test.use({ featureFlags: { FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false } });

        test('Check if tiling switch hides connected configurable parameters - reconfigure active model', async ({
            configurationParametersPage,
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetProjectStatus', (_, res, ctx) => {
                return res(
                    // @ts-expect-error Issue ie openapi types
                    ctx.json(
                        getMockedProjectStatusDTO({
                            tasks: [
                                getMockedProjectStatusTask({ id: '6101254defba22ca453f11d1', ready_to_train: true }),
                            ],
                        })
                    )
                );
            });

            registerApiResponse('GetFullConfiguration', (_, res, ctx) => {
                return res(ctx.status(200), ctx.json(segmentationConfigurationMock));
            });

            await page.goto(CLASSIFICATION_MODELS_URL);
            await configurationParametersPage.openConfigurableParameters();

            await configurationParametersPage.openParametersSection('Instance segmentation');
            await configurationParametersPage.openParametersGroup('Tiling');

            await configurationParametersPage.toggleTiling(true);
            await configurationParametersPage.checkTilingParametersVisibility(true);

            await configurationParametersPage.toggleTiling(false);
            await configurationParametersPage.checkTilingParametersVisibility(false);

            await configurationParametersPage.closeConfigurableParameters();
        });

        test(
            'Check if tiling switch hides connected configurable parameters - new model, manual' + ' configuration',
            async ({ configurationParametersPage, page, registerApiResponse }) => {
                registerApiResponse('GetProjectStatus', (_, res, ctx) => {
                    return res(
                        // @ts-expect-error Issue ie openapi types
                        ctx.json(
                            getMockedProjectStatusDTO({
                                tasks: [
                                    getMockedProjectStatusTask({
                                        id: '60db493fd20945a0046f56d2',
                                        ready_to_train: true,
                                    }),
                                ],
                            })
                        )
                    );
                });

                registerApiResponse('GetTaskConfiguration', (_, res, ctx) => {
                    return res(ctx.status(200), ctx.json(segmentationConfigurationMock.task_chain[0]));
                });

                await page.goto(CLASSIFICATION_MODELS_URL);
                await configurationParametersPage.openTrainNewModelConfigurableParameters();

                await configurationParametersPage.openParametersGroup('Tiling');

                await configurationParametersPage.toggleTiling(true);
                await configurationParametersPage.checkTilingParametersVisibility(true);

                await configurationParametersPage.toggleTiling(false);
                await configurationParametersPage.checkTilingParametersVisibility(false);

                await configurationParametersPage.closeConfigurableParameters();
            }
        );
    });
});
