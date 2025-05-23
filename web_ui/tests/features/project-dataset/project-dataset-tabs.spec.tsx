// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { cloneDeep } from 'lodash-es';

import { DatasetTabActions } from '../../../src/pages/project-details/components/project-dataset/utils';
import { test as baseTest, expect } from '../../fixtures/base-test';
import { extendWithOpenApi } from '../../fixtures/open-api';
import { switchCallsAfter } from '../../utils/api';
import { getDeprecatedModelGroups, getObsoleteModelGroups } from '../project-models/models.mocks';
import {
    expectDatasetMenuItemToBeInvisible,
    expectDatasetMenuItemToBeVisible,
    expectDatasetMoreMenuToBeInvisible,
    expectDatasetMoreMenuToBeVisible,
    expectDatasetNotToBeSelected,
    expectDatasetTabsCountToBe,
    expectDatasetTabsToBeLoaded,
    expectDatasetTabToBeInvisible,
    expectDatasetTabToBeVisible,
    expectDatasetToBeSelected,
    expectURLToContainDatasetId,
} from './expect';
import {
    mockedTestingSet1,
    project,
    projectWithFiveDatasets,
    projectWithSixDatasets,
    projectWithTwoDatasets,
    taskChainProject,
} from './mocks';

const test = extendWithOpenApi(baseTest);

test.describe('Project dataset page', () => {
    test('obsolete active model notification', async ({ page, datasetPage, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(project)));
        });
        const obsoleteAlgorithm = {
            name: 'EfficientNet-B0',
            task_type: 'classification',
            model_size: 200,
            model_template_id: 'classification_efficient',
            gigaflops: 5,
            summary: 'EfficientNet-B0 architecture for classification',
            supports_auto_hpo: true,
            default_algorithm: false,
            performance_category: 'balance',
            lifecycle_stage: 'obsolete',
        };
        const supportedAlgorithms = {
            supported_algorithms: [obsoleteAlgorithm],
        };
        registerApiResponse('GetSupportedAlgorithms', (_, res, ctx) => res(ctx.json(supportedAlgorithms)));
        registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(getObsoleteModelGroups)));

        await datasetPage.goToDatasetURL(project.id, project.datasets[0].id);

        await expectDatasetTabsToBeLoaded(page);

        const notification = page.getByLabel('notification toast');

        await expect(notification.getByText(`Your active model “${obsoleteAlgorithm.name}" is Obsolete`)).toBeVisible();
        await expect(notification.getByRole('button', { name: /Go to models page/i })).toBeVisible();
        await expect(notification.getByRole('button', { name: /dismiss/i })).toBeVisible();
    });

    test('deprecated active model notification', async ({ page, datasetPage, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(project)));
        });
        const deprecatedAlgorithm = {
            name: 'EfficientNet-B0',
            task_type: 'classification',
            model_size: 200,
            model_template_id: 'classification_efficient',
            gigaflops: 5,
            summary: 'EfficientNet-B0 architecture for classification',
            supports_auto_hpo: true,
            default_algorithm: false,
            performance_category: 'balance',
            lifecycle_stage: 'deprecated',
        };
        const supportedAlgorithms = {
            supported_algorithms: [deprecatedAlgorithm],
        };
        registerApiResponse('GetSupportedAlgorithms', (_, res, ctx) => res(ctx.json(supportedAlgorithms)));
        registerApiResponse('GetModelGroups', (_, res, ctx) => res(ctx.json(getDeprecatedModelGroups)));

        await datasetPage.goToDatasetURL(project.id, project.datasets[0].id);

        await expectDatasetTabsToBeLoaded(page);

        const notification = page.getByLabel('notification toast');

        await expect(
            notification.getByText(`Your active model “${deprecatedAlgorithm.name}" is deprecated`)
        ).toBeVisible();
        await expect(notification.getByRole('button', { name: /Go to models page/i })).toBeVisible();
        await expect(notification.getByRole('button', { name: /dismiss/i })).toBeVisible();
    });

    test('Initially should have only one dataset with create button, more menu is not visible', async ({
        page,
        datasetPage,
        registerApiResponse,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(project)));
        });

        const { id, datasets } = project;

        await datasetPage.goToDatasetURL(id, datasets[0].id);

        await expectDatasetTabsToBeLoaded(page);

        await expect(await datasetPage.getCreateDatasetButton()).toBeVisible();
        await expectDatasetMoreMenuToBeInvisible(page);

        await expectDatasetTabsCountToBe(page, 1);
    });

    test('Training dataset should be selected by default', async ({ page, datasetPage, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
        });

        const { id, datasets } = projectWithTwoDatasets;
        const [trainingDataset, testingSet] = datasets;

        await page.goto(
            paths.project.index({
                projectId: id,
                workspaceId: '61011e42d891c82e13ec92da',
                organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
            })
        );

        await expectDatasetTabsToBeLoaded(page);

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));
        await expectDatasetNotToBeSelected(await datasetPage.getDatasetTab(testingSet.name));

        await expectURLToContainDatasetId(page, trainingDataset.id);
    });

    test('Datasets should be URL aware - dataset should change once url changes', async ({
        datasetPage,
        registerApiResponse,
        page,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
        });

        const { id, datasets } = projectWithTwoDatasets;
        const [trainingDataset, testingSet] = datasets;

        await datasetPage.goToDatasetURL(id, trainingDataset.id);
        await expectDatasetTabsToBeLoaded(page);

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));
        await expectDatasetNotToBeSelected(await datasetPage.getDatasetTab(testingSet.name));
        await expectURLToContainDatasetId(page, trainingDataset.id);

        await datasetPage.selectDatasetTab(testingSet.name);

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(testingSet.name));
        await expectDatasetNotToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));

        await expectURLToContainDatasetId(page, testingSet.id);
    });

    test('URL should be DATASET aware - url should change once dataset changes', async ({
        datasetPage,
        registerApiResponse,
        page,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
        });

        const { id, datasets } = projectWithTwoDatasets;
        const [trainingDataset, testingSet] = datasets;

        await datasetPage.goToDatasetURL(id, trainingDataset.id);

        await expectDatasetTabsToBeLoaded(page);

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));
        await expectDatasetNotToBeSelected(await datasetPage.getDatasetTab(testingSet.name));

        await expectURLToContainDatasetId(page, trainingDataset.id);

        await datasetPage.selectDatasetTab(testingSet.name);

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(testingSet.name));
        await expectDatasetNotToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));

        await expectURLToContainDatasetId(page, testingSet.id);
    });

    test('Should create a new testing set and new set should be selected', async ({
        registerApiResponse,
        datasetPage,
        page,
    }) => {
        const switchCallsAfterOne = switchCallsAfter(1);

        registerApiResponse(
            'GetProjectInfo',
            switchCallsAfterOne([
                (_, res, ctx) => {
                    return res(ctx.json(cloneDeep(project)));
                },
                (_, res, ctx) => {
                    return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
                },
            ])
        );

        registerApiResponse('CreateDataset', (_req, res, ctx) => {
            // @ts-expect-error we return dataset in a good shape
            return res(ctx.json(mockedTestingSet1));
        });

        await datasetPage.goToDatasetURL(project.id, project.datasets[0].id);

        await expectDatasetTabsToBeLoaded(page);

        await datasetPage.createDataset();

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(projectWithTwoDatasets.datasets[1].name));
    });

    test('Should edit dataset name correctly', async ({ registerApiResponse, datasetPage, page }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
        });

        const [trainingDataset, testingSet] = projectWithTwoDatasets.datasets;
        await datasetPage.goToDatasetURL(project.id, trainingDataset.id);

        await expectDatasetTabsToBeLoaded(page);

        await datasetPage.selectDatasetTab(testingSet.name);

        await datasetPage.selectDatasetTabMenuItem(testingSet.name, DatasetTabActions.UpdateDataset);

        const newTestingSetName = 'Cool testing set';

        await page.getByRole('textbox', { name: /Dataset name/i }).fill(newTestingSetName);
        await page.getByRole('button', { name: /confirm/i }).click();

        await expect(await datasetPage.getDatasetTab(newTestingSetName)).toBeVisible();
    });

    test('Should delete testing set correctly', async ({ registerApiResponse, datasetPage, page }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
        });

        const [trainingDataset, testingSet] = projectWithTwoDatasets.datasets;
        await datasetPage.goToDatasetURL(project.id, testingSet.id);

        await expectDatasetTabsToBeLoaded(page);

        await expectDatasetTabsCountToBe(page, projectWithTwoDatasets.datasets.length);

        await datasetPage.selectDatasetTabMenuItem(testingSet.name, DatasetTabActions.DeleteDataset);

        await page.getByRole('button', { name: /delete/i }).click();

        await expectDatasetTabsCountToBe(page, projectWithTwoDatasets.datasets.length - 1);
        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));
    });

    test('Should not display more menu if there are less than six datasets', async ({
        registerApiResponse,
        datasetPage,
        page,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithFiveDatasets)));
        });

        const [trainingDataset] = projectWithFiveDatasets.datasets;
        await datasetPage.goToDatasetURL(project.id, trainingDataset.id);

        await expectDatasetTabsToBeLoaded(page);

        await expectDatasetMoreMenuToBeInvisible(page);
    });

    test('Should display more menu if there are more than five datasets', async ({
        registerApiResponse,
        datasetPage,
        page,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithSixDatasets)));
        });

        const trainingDataset = projectWithSixDatasets.datasets[0];

        await datasetPage.goToDatasetURL(project.id, trainingDataset.id);

        await expectDatasetTabsToBeLoaded(page);

        await expectDatasetMoreMenuToBeVisible(await datasetPage.getDatasetMoreMenu());
    });

    test('Should swap last pinned dataset with collapsed dataset if collapsed gets selected', async ({
        registerApiResponse,
        datasetPage,
        page,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithSixDatasets)));
        });

        const trainingDataset = projectWithSixDatasets.datasets[0];
        const secondToLastTestingSet = projectWithSixDatasets.datasets[projectWithSixDatasets.datasets.length - 2];
        const lastTestingSet = projectWithSixDatasets.datasets[projectWithSixDatasets.datasets.length - 1];

        await datasetPage.goToDatasetURL(project.id, trainingDataset.id);

        await expectDatasetTabsToBeLoaded(page);

        await expectDatasetTabToBeVisible(await datasetPage.getDatasetTab(secondToLastTestingSet.name));
        await expectDatasetTabToBeInvisible(await datasetPage.getDatasetTab(lastTestingSet.name));

        const datasetMoreMenu = await datasetPage.getDatasetMoreMenu();
        await datasetMoreMenu.click();
        await page.getByRole('option', { name: lastTestingSet.name }).click();

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(lastTestingSet.name));
        await expectDatasetTabToBeInvisible(await datasetPage.getDatasetTab(secondToLastTestingSet.name));
    });

    test('Should move collapsed dataset to pinned datasets if pinned dataset gets deleted', async ({
        registerApiResponse,
        datasetPage,
        page,
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(projectWithSixDatasets)));
        });

        const trainingDataset = projectWithSixDatasets.datasets[0];
        const testingSet = projectWithSixDatasets.datasets[1];
        const lastTestingSet = projectWithSixDatasets.datasets[projectWithSixDatasets.datasets.length - 1];

        await datasetPage.goToDatasetURL(project.id, testingSet.id);

        await expectDatasetTabsToBeLoaded(page);

        await datasetPage.selectDatasetTabMenuItem(testingSet.name, DatasetTabActions.DeleteDataset);
        await page.getByRole('button', { name: /delete/i }).click();

        await expectDatasetToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));
        await expectDatasetTabToBeVisible(await datasetPage.getDatasetTab(lastTestingSet.name));
    });

    test.describe('Dataset tab actions', async () => {
        test('Task chain project should not have "Import dataset" action', async ({
            registerApiResponse,
            datasetPage,
            page,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => {
                return res(ctx.json(cloneDeep(taskChainProject)));
            });

            const { id, datasets } = taskChainProject;

            await datasetPage.goToDatasetURL(id, datasets[0].id);

            await expectDatasetTabsToBeLoaded(page);

            await datasetPage.openDatasetTabMenu(datasets[0].name);

            await expectDatasetMenuItemToBeInvisible(page, DatasetTabActions.ImportDataset);
            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.ExportDataset);
        });

        test('Only selected dataset should have actions', async ({ registerApiResponse, datasetPage, page }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => {
                return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
            });

            const { id, datasets } = projectWithTwoDatasets;
            const [trainingDataset, testingSet] = datasets;

            await datasetPage.goToDatasetURL(id, trainingDataset.id);

            await expectDatasetTabsToBeLoaded(page);

            await expectDatasetToBeSelected(await datasetPage.getDatasetTab(trainingDataset.name));

            await expect(await datasetPage.getDatasetTabMenu(trainingDataset.name)).toBeVisible();
            await expect(await datasetPage.getDatasetTabMenu(testingSet.name)).not.toBeVisible();
        });

        test('Training dataset should have only IMPORT DATASET action if there are no media', async ({
            registerApiResponse,
            datasetPage,
            page,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => {
                return res(ctx.json(cloneDeep(project)));
            });

            registerApiResponse('FilterMedia', (_, res, ctx) => {
                return res(
                    ctx.json({
                        media: [],
                        total_images: 0,
                        total_matched_images: 0,
                        total_matched_video_frames: 0,
                        total_matched_videos: 0,
                        total_videos: 0,
                    })
                );
            });

            const { id, datasets } = project;
            const [dataset] = datasets;

            await datasetPage.goToDatasetURL(id, dataset.id);

            await expectDatasetTabsToBeLoaded(page);

            await datasetPage.openDatasetTabMenu(dataset.name);

            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.ImportDataset);
            await expectDatasetMenuItemToBeInvisible(page, DatasetTabActions.DeleteDataset);
            await expectDatasetMenuItemToBeInvisible(page, DatasetTabActions.ExportDataset);
            await expectDatasetMenuItemToBeInvisible(page, DatasetTabActions.UpdateDataset);
        });

        test('Training dataset should have IMPORT DATASET and EXPORT DATASET actions', async ({
            registerApiResponse,
            datasetPage,
            page,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => {
                return res(ctx.json(cloneDeep(project)));
            });

            const { id, datasets } = project;
            const [dataset] = datasets;

            await datasetPage.goToDatasetURL(id, dataset.id);

            await expectDatasetTabsToBeLoaded(page);

            await datasetPage.openDatasetTabMenu(dataset.name);

            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.ImportDataset);
            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.ExportDataset);
            await expectDatasetMenuItemToBeInvisible(page, DatasetTabActions.DeleteDataset);
            await expectDatasetMenuItemToBeInvisible(page, DatasetTabActions.UpdateDataset);
        });

        // eslint-disable-next-line max-len
        test('Testing set should have IMPORT DATASET, EXPORT DATASET, UPDATE DATASET and DELETE DATASET actions', async ({
            registerApiResponse,
            datasetPage,
            page,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => {
                return res(ctx.json(cloneDeep(projectWithTwoDatasets)));
            });

            const { id, datasets } = projectWithTwoDatasets;
            const [, testingSet] = datasets;

            await datasetPage.goToDatasetURL(id, testingSet.id);

            await expectDatasetTabsToBeLoaded(page);

            await datasetPage.openDatasetTabMenu(testingSet.name);

            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.ImportDataset);
            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.ExportDataset);
            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.DeleteDataset);
            await expectDatasetMenuItemToBeVisible(page, DatasetTabActions.UpdateDataset);
        });
    });
});
