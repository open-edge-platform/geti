// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { rest } from 'msw';

import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { server } from '../../annotations/services/test-utils';
import { API_URLS } from '../../services/urls';
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
