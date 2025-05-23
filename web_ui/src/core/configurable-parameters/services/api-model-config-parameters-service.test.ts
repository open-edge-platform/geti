// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { rest } from 'msw';

import { apiRequestUrl } from '../../../../packages/core/src/services/test-utils';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { server } from '../../annotations/services/test-utils';
import { API_URLS } from '../../services/urls';
import { createApiModelConfigParametersService } from './api-model-config-parameters-service';
import {
    mockedConfigParamData,
    mockedConfigParamDTO,
    mockedConfigTaskChainDTO,
    mockedReadOnlyConfigTaskChainData,
} from './test-utils';

jest.mock('uuid', () => ({
    v4: jest.fn(() => 1),
}));

describe('API model config parameters service', () => {
    const projectId = 'test-project';
    const projectIdentifier = getMockedProjectIdentifier({ projectId });

    const taskId = 'task-id';
    const modelId = 'model-id';
    const { getModelConfigParameters, getConfigParameters } = createApiModelConfigParametersService();

    it('should get configurable parameters for specified model', async () => {
        const modelUrl = API_URLS.MODEL_CONFIG_PARAMETERS(projectIdentifier, taskId, modelId);

        server.use(rest.get(apiRequestUrl(modelUrl), (_req, res, ctx) => res(ctx.json(mockedConfigTaskChainDTO))));

        const modelConfigParameters = await getModelConfigParameters(projectIdentifier, taskId, modelId);

        expect(modelConfigParameters).toEqual(mockedReadOnlyConfigTaskChainData);
    });

    it('should get configurable parameters for the tasks', async () => {
        const tasksConfigUrl = API_URLS.CONFIGURATION_PARAMETERS(projectIdentifier);

        server.use(rest.get(apiRequestUrl(tasksConfigUrl), (_req, res, ctx) => res(ctx.json(mockedConfigParamDTO))));

        const configParameters = await getConfigParameters(projectIdentifier);

        expect(configParameters).toEqual(mockedConfigParamData);
    });
});
