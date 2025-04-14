// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as fs from 'fs';

import { JobDTO } from '../../src/core/jobs/dtos/jobs-dto.interface';
import { JobState } from '../../src/core/jobs/jobs.const';
import { OpenApiRequest } from '../../src/core/server/types';
import type {
    UserGlobalSettings,
    UserProjectSettings,
} from '../../src/core/user-settings/services/user-settings.interface';
import { delay } from '../../src/shared/utils';
import { ApiResponse, OpenApiFixtures } from '../fixtures/open-api';

export const switchCallsAfter =
    (limit: number) =>
    (callbacks: ApiResponse[]): ApiResponse => {
        let counter = -1;
        let currentPosition = -1;

        return async (req, res, ctx) => {
            counter += 1;
            currentPosition = counter % limit === 0 ? (currentPosition += 1) : currentPosition;
            currentPosition = currentPosition < callbacks.length ? currentPosition : callbacks.length - 1;

            return callbacks[currentPosition](req, res, ctx);
        };
    };

export const setTusProgress =
    (total: number, current: number, delayTime = 0): ApiResponse =>
    async (_, res, ctx) => {
        await delay(delayTime);

        return res(ctx.set('Upload-offset', `${current}`), ctx.set('Upload-Length', `${total}`));
    };

export const registerStoreSettings = (
    registerApiResponse: OpenApiFixtures['registerApiResponse'],
    initConfig?: Partial<UserGlobalSettings | UserProjectSettings>
) => {
    const newSettings: { [k: string]: Record<string, unknown> } = {};

    registerApiResponse('SetSettings', (req, res, ctx) => {
        const key = JSON.stringify(req.query);
        newSettings[key] = req.body;

        return res(ctx.json(req.body));
    });

    registerApiResponse('GetSettings', (req, res, ctx) => {
        const key = JSON.stringify(req.query);
        const data = newSettings[key] ? newSettings[key] : { settings: JSON.stringify(initConfig) };

        return res(ctx.json(data));
    });
};

export const registerJobList = (registerApiResponse: OpenApiFixtures['registerApiResponse'], job: JobDTO) => {
    const newJob = { ...job };

    registerApiResponse('GetJob', (_: OpenApiRequest<'GetJob'>, res, ctx) => res(ctx.json(newJob)));
    registerApiResponse('CancelJob', (_: OpenApiRequest<'GetJob'>, res, ctx) => {
        newJob.state = JobState.CANCELLED;

        return res(ctx.status(200));
    });

    registerApiResponse('GetJobs', (_: OpenApiRequest<'GetJobs'>, res, ctx) =>
        res(
            ctx.json({
                jobs: [newJob],
                jobs_count: {
                    n_scheduled_jobs: 1,
                    n_running_jobs: 0,
                    n_finished_jobs: 0,
                    n_failed_jobs: 0,
                    n_cancelled_jobs: 0,
                },
            })
        )
    );
};

export const registerFullImage = (registerApiResponse: OpenApiFixtures['registerApiResponse'], pathToFile: string) => {
    registerApiResponse('DownloadFullImage', async (_, res, ctx) => {
        const imageBuffer = fs.readFileSync(pathToFile);

        return res(
            ctx.set('Content-Length', imageBuffer.byteLength.toString()),
            ctx.set('Content-Type', 'image/jpeg'),
            // @ts-expect-error ignore
            ctx.body(imageBuffer)
        );
    });
};

export const registerFullVideoFrame = (
    registerApiResponse: OpenApiFixtures['registerApiResponse'],
    pathToFile: string
) => {
    registerApiResponse('DownloadVideoFrameFull', async (_, res, ctx) => {
        const imageBuffer = fs.readFileSync(pathToFile);

        return res(
            ctx.set('Content-Length', imageBuffer.byteLength.toString()),
            ctx.set('Content-Type', 'image/jpeg'),
            // @ts-expect-error ignore
            ctx.body(imageBuffer)
        );
    });
};
