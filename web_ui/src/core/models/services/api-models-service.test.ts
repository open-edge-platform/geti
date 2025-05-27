// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { rest } from 'msw';

import { API_URLS } from '../../../../packages/core/src/services/urls';
import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { server } from '../../annotations/services/test-utils';
import { mockedSupportedAlgorithms } from '../../supported-algorithms/services/test-utils';
import { createApiModelsService } from './api-models-service';
import { mockedArchitectureModels, mockedArchitectureModelsDTO } from './test-utils';

describe('Api models service', () => {
    const { getModels } = createApiModelsService();
    const projectIdentifier = getMockedProjectIdentifier();

    it('Should get models', async () => {
        server.use(
            rest.get(API_URLS.MODELS(projectIdentifier), (_req, res, ctx) =>
                res(ctx.json({ model_groups: mockedArchitectureModelsDTO }))
            )
        );

        const result = await getModels(projectIdentifier, {
            [mockedArchitectureModelsDTO[0].task_id]: mockedSupportedAlgorithms,
            [mockedArchitectureModelsDTO[1].task_id]: mockedSupportedAlgorithms,
        });

        expect(result).toEqual(mockedArchitectureModels);
    });

    it('Should only return models that are not corrupt', async () => {
        const responseWithOneCorruptedModel = [
            ...mockedArchitectureModelsDTO,
            {
                id: undefined, // corrupted data
                name: 'ATSS',
                model_template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR',
                task_id: '1236',
                models: [],
            },
        ];
        server.use(
            rest.get(API_URLS.MODELS(projectIdentifier), (_req, res, ctx) =>
                res(ctx.json({ model_groups: responseWithOneCorruptedModel }))
            )
        );

        const result = await getModels(projectIdentifier, {
            [responseWithOneCorruptedModel[0].task_id]: mockedSupportedAlgorithms,
            [responseWithOneCorruptedModel[1].task_id]: mockedSupportedAlgorithms,
            [responseWithOneCorruptedModel[2].task_id]: mockedSupportedAlgorithms,
        });

        expect(result).toEqual(mockedArchitectureModels);
    });
});
