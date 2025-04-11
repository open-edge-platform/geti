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

import { server } from '../../annotations/services/test-utils';
import { apiRequestUrl } from '../../services/test-utils';
import { API_URLS } from '../../services/urls';
import { createApiStatusService } from './api-status-service';

const mockedStatusResponse = {
    freeSpace: 35,
    totalSpace: 100,
    runningJobs: 3,
};

describe('API status service', () => {
    const statusUrl = API_URLS.STATUS();
    const service = createApiStatusService();

    it('check if status is fetched properly', async () => {
        server.use(
            rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                res(
                    ctx.json({
                        free_space: '35 GB',
                        n_running_jobs: 3,
                        storage: {
                            free_space: 35,
                            total_space: 100,
                        },
                    })
                )
            )
        );

        const response = await service.getStatus();

        expect(response).toEqual(mockedStatusResponse);
    });

    it('check if generic status is returned in the case of a 403 response', async () => {
        server.use(
            rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                res(
                    ctx.status(403),
                    ctx.json({
                        free_space: '35 GB',
                        n_running_jobs: 3,
                        storage: {
                            free_space: 35,
                            total_space: 100,
                        },
                    })
                )
            )
        );

        const response = await service.getStatus();

        expect(response).toEqual({
            freeSpace: 0,
            totalSpace: 0,
            runningJobs: 0,
        });
    });

    it('assumes there is infinite space if no storage information is provided', async () => {
        server.use(
            rest.get(apiRequestUrl(statusUrl), (_req, res, ctx) =>
                res(
                    ctx.json({
                        n_running_jobs: 3,
                    })
                )
            )
        );

        const response = await service.getStatus();

        expect(response).toEqual({
            freeSpace: Infinity,
            totalSpace: Infinity,
            runningJobs: 3,
        });
    });
});
