// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { rest } from 'msw';

import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { server } from '../../annotations/services/test-utils';
import { API_URLS } from '../../services/urls';
import { createApiSupportedAlgorithmsService } from './api-supported-algorithms-service';
import { mockedSupportedAlgorithms, mockedSupportedAlgorithmsDTO } from './test-utils';

describe('Supported algorithms service', () => {
    it('should get project supported algorithm', async () => {
        const mockedProjectIdentifier = getMockedProjectIdentifier();

        server.use(
            rest.get(API_URLS.PROJECT_SUPPORTED_ALGORITHMS(mockedProjectIdentifier), (_req, res, ctx) =>
                res(
                    ctx.json({
                        supported_algorithms: mockedSupportedAlgorithmsDTO,
                    })
                )
            )
        );

        const { getProjectSupportedAlgorithms } = createApiSupportedAlgorithmsService();
        const supportedAlgorithms = await getProjectSupportedAlgorithms(mockedProjectIdentifier);

        expect(supportedAlgorithms).toEqual(mockedSupportedAlgorithms);
    });
});
