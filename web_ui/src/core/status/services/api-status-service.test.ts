// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
