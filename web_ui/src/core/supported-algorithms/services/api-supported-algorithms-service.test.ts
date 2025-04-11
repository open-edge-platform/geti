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
