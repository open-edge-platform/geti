// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook } from '@testing-library/react';

import { useGetRunningJobs, useGetScheduledJobs } from '../../../../../../core/jobs/hooks/use-jobs.hook';
import { JobState, JobType } from '../../../../../../core/jobs/jobs.const';
import { getMockedJob } from '../../../../../../test-utils/mocked-items-factory/mocked-jobs';
import { RequiredProviders } from '../../../../../../test-utils/required-providers-render';
import { useTrainingProgress } from './use-training-progress.hook';

jest.mock('../../../../../../core/jobs/hooks/use-jobs.hook', () => ({
    useGetRunningJobs: jest.fn(() => ({ data: { pages: [] } })),
    useGetScheduledJobs: jest.fn(() => ({ data: { pages: [] } })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({
        projectId: 'project-id',
        workspaceId: 'workspace_1',
        organizationId: 'organization-id',
    })),
}));

describe('useTrainingProgress', () => {
    const taskId = 'detection-id';

    const wrapper = ({ children }: { children: ReactNode }) => {
        return <RequiredProviders>{children}</RequiredProviders>;
    };

    it('should not return progress when there are no running or scheduled jobs', async () => {
        // @ts-expect-error We don't care about mocking other rq vars
        jest.mocked(useGetRunningJobs).mockReturnValue({ data: { pages: [] } });

        const { result } = renderHook(() => useTrainingProgress(taskId), { wrapper });

        expect(result.current.showTrainingProgress).toBe(false);
    });

    it('should return a list of running job items when there is running job assigned to the task', async () => {
        const jobs = [
            getMockedJob({
                state: JobState.RUNNING,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId,
                        modelArchitecture: 'YoloV4',
                        name: 'Detection',
                        datasetStorageId: 'dataset-storage-id',
                        modelTemplateId: 'template-id',
                    },
                    project: {
                        id: '123',
                        name: 'example project',
                    },
                    trainedModel: {
                        modelId: 'model-id',
                    },
                },
            }),
            getMockedJob({
                state: JobState.RUNNING,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId: 'segmentation-id',
                        modelArchitecture: 'YoloV4',
                        name: 'Segmentation',
                        datasetStorageId: 'dataset-storage-id',
                        modelTemplateId: 'template-id',
                    },
                    project: {
                        id: '123',
                        name: 'example project',
                    },
                    trainedModel: {
                        modelId: 'model-id',
                    },
                },
            }),
        ];

        // @ts-expect-error We don't care about mocking other rq vars
        jest.mocked(useGetRunningJobs).mockReturnValue({ data: { pages: [{ jobs }] }, isSuccess: true });

        const { result } = renderHook(() => useTrainingProgress(taskId), { wrapper });

        expect(result.current.showTrainingProgress).toBe(true);
        // returns only the job assigned to the task
        expect('trainingDetails' in result.current && result.current.trainingDetails).toEqual([jobs[0]]);
    });

    it('should return a list of scheduled jobs items when there is scheduled job assigned to the task', async () => {
        const jobs = [
            getMockedJob({
                state: JobState.SCHEDULED,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId,
                        modelArchitecture: 'YoloV4',
                        name: 'Detection',
                        datasetStorageId: 'dataset-storage-id',
                        modelTemplateId: 'template-id',
                    },
                    project: {
                        id: '123',
                        name: 'example project',
                    },
                    trainedModel: {
                        modelId: 'detection-model-id',
                    },
                },
            }),
            getMockedJob({
                state: JobState.SCHEDULED,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId: 'segmentation-id',
                        modelArchitecture: 'YoloV4',
                        name: 'Segmentation',
                        datasetStorageId: 'dataset-storage-id',
                        modelTemplateId: 'template-id',
                    },
                    project: {
                        id: '123',
                        name: 'example project',
                    },
                    trainedModel: {
                        modelId: 'segmentation-model-id',
                    },
                },
            }),
        ];

        // @ts-expect-error We don't care about mocking other rq vars
        jest.mocked(useGetScheduledJobs).mockReturnValue({ data: { pages: [{ jobs }] }, isSuccess: true });
        // @ts-expect-error We don't care about mocking other rq vars
        jest.mocked(useGetRunningJobs).mockReturnValue({ data: { pages: [] }, isSuccess: false });

        const { result } = renderHook(() => useTrainingProgress(taskId), { wrapper });

        expect(result.current.showTrainingProgress).toBe(true);
        // returns only the job assigned to the task
        expect('trainingDetails' in result.current && result.current.trainingDetails).toEqual([jobs[0]]);
    });

    it('should not return running job item when there is running job but assigned to another task', async () => {
        const jobs = [
            getMockedJob({
                state: JobState.RUNNING,
                type: JobType.TRAIN,
                metadata: {
                    task: {
                        taskId: 'segmentation-id',
                        modelArchitecture: 'YoloV4',
                        name: 'Segmentation',
                        datasetStorageId: 'dataset-storage-id',
                        modelTemplateId: 'template-id',
                    },
                    project: {
                        id: '123',
                        name: 'example project',
                    },
                    trainedModel: {
                        modelId: 'model-id',
                    },
                },
            }),
        ];

        // @ts-expect-error We don't care about mocking other rq vars
        jest.mocked(useGetRunningJobs).mockReturnValue({ data: { pages: [{ jobs }] } });
        // @ts-expect-error We don't care about mocking other rq vars
        jest.mocked(useGetScheduledJobs).mockReturnValue({ data: { pages: [] }, isSuccess: false });

        const { result } = renderHook(() => useTrainingProgress(taskId), { wrapper });

        expect(result.current.showTrainingProgress).toBe(false);
    });
});
