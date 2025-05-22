// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { cloneDeep, orderBy } from 'lodash-es';

import { test as baseTest } from '../../fixtures/base-test';
import { extendWithOpenApi } from '../../fixtures/open-api';
import { supportedAlgorithms } from '../../fixtures/open-api/mocks';
import { ProjectModelsPage } from '../../fixtures/page-objects/models-page';
import { project } from '../../mocks/classification/mocks';
import { getModelDetail, getModelGroup, getModelGroups } from './models.mocks';

interface ModelsFixtures {
    modelsPage: ProjectModelsPage;
}

export const testWithModels = extendWithOpenApi(baseTest).extend<ModelsFixtures>({
    modelsPage: async ({ modelsPage, registerApiResponse }, use) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            return res(ctx.json(cloneDeep(project)));
        });

        registerApiResponse('GetSupportedAlgorithms', (_, res, ctx) => {
            return res(ctx.status(200), ctx.json(supportedAlgorithms));
        });

        registerApiResponse('GetModelGroups', (_, res, ctx) => {
            const task = (project.pipeline?.tasks ?? []).find(({ task_type }) => task_type !== 'dataset');

            const algorithmsPerTask =
                supportedAlgorithms.supported_algorithms?.filter(({ task_type }) => task_type === task?.task_type) ??
                [];

            const sortedAlgorithms = orderBy(algorithmsPerTask, 'gigaflops', 'asc');

            const model_groups = getModelGroups.model_groups?.map((modelGroup) => {
                return { ...modelGroup, task_id: task?.id, model_template_id: sortedAlgorithms[0].model_template_id };
            });

            return res(ctx.status(200), ctx.json({ model_groups }));
        });

        registerApiResponse('GetModelGroup', (_, res, ctx) => {
            return res(ctx.status(200), ctx.json(getModelGroup));
        });

        registerApiResponse('GetModelDetail', (_, res, ctx) => {
            return res(ctx.status(200), ctx.json(getModelDetail));
        });

        await use(modelsPage);
    },
});

export const testWithModelsApiExamples = extendWithOpenApi(baseTest).extend<ModelsFixtures>({
    modelsPage: async ({ modelsPage, registerApiExample }, use) => {
        registerApiExample('GetProjectInfo', 'Task chain creation response');
        registerApiExample('GetSupportedAlgorithms', 'Supported algorithms');

        registerApiExample('GetModelGroups', 'Model list response');
        registerApiExample('GetModelDetail', 'Model detail response');
        registerApiExample('FilterMediaInTrainingRevision', 'Combined media list response');

        await use(modelsPage);
    },
});
