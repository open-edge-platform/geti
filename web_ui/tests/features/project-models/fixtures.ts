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

import cloneDeep from 'lodash/cloneDeep';

import { sortAscending } from '../../../src/shared/utils';
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

            const sortedAlgorithms = sortAscending(algorithmsPerTask, 'gigaflops');

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
