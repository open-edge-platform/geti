// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Page } from '@playwright/test';
import { ResponseComposition } from 'msw';

import {
    DatasetImportSupportedProjectTypeDTO,
    DatasetImportWarningDTO,
} from '../../../src/core/datasets/dtos/dataset.interface';
import {
    JobGeneralPropsDTO,
    JobImportDatasetToExistingProjectStatusDTO,
    JobImportDatasetToNewProjectStatusDTO,
    JobPrepareDatasetImportNewProjectStatusDTO,
    JobPrepareDatasetToExistingProjectStatusDTO,
    JobStepDTO,
} from '../../../src/core/jobs/dtos/jobs-dto.interface';
import { JobState, JobStepState, JobType } from '../../../src/core/jobs/jobs.const';
import { operations } from '../../../src/core/server/generated/schemas';
import { OpenApiRequest } from '../../../src/core/server/types';
import { OpenApiFixtures } from '../../fixtures/open-api';
import { switchCallsAfter } from '../../utils/api';

export const getMockedJob = (job: Partial<JobGeneralPropsDTO> = {}): JobGeneralPropsDTO => {
    const steps =
        job.state === JobState.FAILED
            ? [
                  {
                      index: 0,
                      message: 'Something went wrong. Please try again',
                      progress: 0.0,
                      state: JobStepState.FAILED,
                      step_name: 'Failed step',
                  },
              ]
            : [
                  {
                      index: 0,
                      message: 'test',
                      progress: -1,
                      state: JobStepState.WAITING,
                      step_name: 'test',
                  },
              ];

    return {
        id: 'job-1',
        name: 'Mocked task job',
        state: JobState.SCHEDULED,
        start_time: '2023-10-15T11:54:48.273000+00:00',
        author: 'admin@intel.com',
        creation_time: '2023-10-15T11:54:48.273000+00:00',
        end_time: null,
        steps,
        cancellation_info: {
            is_cancelled: false,
            user_uid: null,
            cancel_time: null,
            cancellable: true,
        },
        ...job,
    };
};

export type GetMockedPreparingJob = (
    job?: Partial<JobPrepareDatasetImportNewProjectStatusDTO>
) => JobPrepareDatasetImportNewProjectStatusDTO;

export type GetMockedExistingProjectPreparingJob = (
    job?: Partial<JobPrepareDatasetToExistingProjectStatusDTO>
) => JobPrepareDatasetToExistingProjectStatusDTO;

export type GetMockedImportingJob = (
    job?: Partial<JobImportDatasetToNewProjectStatusDTO>
) => JobImportDatasetToNewProjectStatusDTO;

export type GetMockedExistingProjectImportingJob = (
    job?: Partial<JobImportDatasetToExistingProjectStatusDTO>
) => JobImportDatasetToExistingProjectStatusDTO;

export const getMockedPreparingJob: GetMockedPreparingJob = (
    job: Partial<JobPrepareDatasetImportNewProjectStatusDTO> = {}
): JobPrepareDatasetImportNewProjectStatusDTO => {
    return {
        ...getMockedJob(job),
        type: JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT,
        metadata: {
            warnings: job.metadata?.warnings,
            supported_project_types: job.metadata?.supported_project_types,
        },
    };
};

export const getMockedExistingProjectPreparingJob: GetMockedExistingProjectPreparingJob = (
    job: Partial<JobPrepareDatasetToExistingProjectStatusDTO> = {}
): JobPrepareDatasetToExistingProjectStatusDTO => {
    return {
        ...getMockedJob(job),
        type: JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT,
        metadata: {
            warnings: job.metadata?.warnings,
            labels: job.metadata?.labels,
        },
    };
};

export const getMockedImportingJob: GetMockedImportingJob = (
    job: Partial<JobImportDatasetToNewProjectStatusDTO> = {}
): JobImportDatasetToNewProjectStatusDTO => {
    return {
        ...getMockedJob(job),
        type: JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT,
        metadata: {
            project_id: job.metadata?.project_id,
        },
    };
};

export const getMockedExistingProjectImportingJob: GetMockedExistingProjectImportingJob = (
    job: Partial<JobImportDatasetToExistingProjectStatusDTO> = {}
): JobImportDatasetToExistingProjectStatusDTO => {
    return {
        ...getMockedJob(job),
        type: JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT,
        metadata: {
            dataset: job.metadata?.dataset,
        },
    };
};

export const registerJobResponses = (
    registerApiResponse: OpenApiFixtures['registerApiResponse'],
    jobId: string,
    mockedHandlerJob:
        | GetMockedPreparingJob
        | GetMockedExistingProjectPreparingJob
        | GetMockedImportingJob
        | GetMockedExistingProjectImportingJob,
    data: {
        state?: JobState | undefined;
        metadata:
            | { project_id?: string }
            | {
                  labels?: string[];
                  warnings?: DatasetImportWarningDTO[];
                  supported_project_types?: DatasetImportSupportedProjectTypeDTO[];
              }
            | {
                  dataset?: {
                      id: string;
                      name: string;
                      use_for_training: boolean;
                      creation_time: string;
                  };
              };
        steps?: JobStepDTO[];
    }
) => {
    const switchAfterTwoCalls = switchCallsAfter(2);

    registerApiResponse(
        'GetJob',
        switchAfterTwoCalls([
            (_: OpenApiRequest<keyof operations>, res: ResponseComposition, ctx) => {
                return res(
                    ctx.json(mockedHandlerJob({ id: jobId, state: JobState.SCHEDULED, steps: data.steps ?? [] }))
                );
            },
            (_: OpenApiRequest<keyof operations>, res: ResponseComposition, ctx) => {
                return res(ctx.json(mockedHandlerJob({ id: jobId, state: JobState.RUNNING, steps: data.steps ?? [] })));
            },
            (_: OpenApiRequest<keyof operations>, res: ResponseComposition, ctx) => {
                return res(
                    ctx.json(
                        mockedHandlerJob({
                            id: jobId,
                            state: data.state ?? JobState.FINISHED,
                            metadata: data.metadata,
                            steps: data.steps ?? [],
                        })
                    )
                );
            },
        ])
    );
};

export const waitForJobToFinish = async (page: Page, preparingJobId: string, state = JobState.FINISHED) => {
    await page.waitForResponse(async (response) => {
        if (!response.url().includes(`/jobs/${preparingJobId}`)) {
            return false;
        }

        const jobResponse = await response.json();
        return jobResponse.state === state;
    });
};

export const getLocalStorage = async (page: Page, key: string) => {
    const localStorage = await page.evaluate(() => JSON.parse(JSON.stringify(window.localStorage)));
    return JSON.parse(localStorage[key]);
};
