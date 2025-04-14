// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { JobState, JobStepState, JobType } from '../../../../core/jobs/jobs.const';
import { JobCount } from '../../../../core/jobs/jobs.interface';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import {
    formatJobDuration,
    getAllJobs,
    getJobDuration,
    getNameFromJob,
    getStepProgress,
    getStepProgressNumber,
    isJobCancel,
    isJobCancelOrFailed,
    isJobDone,
    isJobExportDone,
    isJobSettled,
    isRunningTrainingJob,
    JOB_STATE_TO_DISCARD_TYPE,
} from './utils';

describe('Job scheduler utils', (): void => {
    describe('Text on discard button', (): void => {
        it('should show "Cancel" on running jobs discard button', (): void => {
            expect(JOB_STATE_TO_DISCARD_TYPE[JobState.RUNNING]).toBe('Cancel');
        });

        it('should show "Cancel" on scheduled jobs discard button', (): void => {
            expect(JOB_STATE_TO_DISCARD_TYPE[JobState.SCHEDULED]).toBe('Cancel');
        });

        it('should show "Delete" on failed jobs discard button', (): void => {
            expect(JOB_STATE_TO_DISCARD_TYPE[JobState.FAILED]).toBe('Delete');
        });

        it('should show "Delete" on finished jobs discard button', (): void => {
            expect(JOB_STATE_TO_DISCARD_TYPE[JobState.FINISHED]).toBe('Delete');
        });

        it('should show "Delete" on Cancelled jobs discard button', (): void => {
            expect(JOB_STATE_TO_DISCARD_TYPE[JobState.CANCELLED]).toBe('Delete');
        });
    });

    it('should right trim "task" substring from job name', (): void => {
        expect(getNameFromJob('some name task')).toBe('some name');
        expect(getNameFromJob('some name title')).toBe('some name title');
    });

    it('should properly show step progress presentation', (): void => {
        expect(getStepProgress(72)).toBe('72%');
        expect(getStepProgress(81.567)).toBe('82%');
        expect(getStepProgress(-1)).toBe('');
        expect(getStepProgress(-100)).toBe('');
        expect(getStepProgress(null)).toBe('');
        expect(getStepProgress(undefined)).toBe('');
    });

    it('should properly get step progress', (): void => {
        expect(getStepProgressNumber(72)).toBe(72);
        expect(getStepProgressNumber(81.567)).toBe(81.567);
        expect(getStepProgressNumber(-1)).toBe(0);
        expect(getStepProgressNumber(-100)).toBe(0);
        expect(getStepProgressNumber(null)).toBe(0);
        expect(getStepProgressNumber(undefined)).toBe(0);
    });

    it('should return an array of jobs for infinite query or empty array', (): void => {
        expect(getAllJobs(undefined)).toHaveLength(0);
        expect(
            getAllJobs({
                pages: [
                    { jobs: [getMockedJob()], jobsCount: {} as JobCount, nextPage: undefined },
                    { jobs: [getMockedJob()], jobsCount: {} as JobCount, nextPage: undefined },
                    { jobs: [getMockedJob()], jobsCount: {} as JobCount, nextPage: undefined },
                ],
                pageParams: [],
            })
        ).toHaveLength(3);
    });

    it.each([
        {
            state: JobState.RUNNING,
            stateStr: JobState.RUNNING.toUpperCase(),
            type: JobType.TRAIN,
            typeStr: JobType.TRAIN.toUpperCase(),
            result: true,
            resultStr: 'define',
        },
        {
            state: JobState.RUNNING,
            stateStr: JobState.RUNNING.toUpperCase(),
            type: JobType.TEST,
            typeStr: JobType.TEST.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.RUNNING,
            stateStr: JobState.RUNNING.toUpperCase(),
            type: JobType.OPTIMIZATION_POT,
            typeStr: JobType.OPTIMIZATION_POT.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },

        {
            state: JobState.FAILED,
            stateStr: JobState.FAILED.toUpperCase(),
            type: JobType.TRAIN,
            typeStr: JobType.TRAIN.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.FAILED,
            stateStr: JobState.FAILED.toUpperCase(),
            type: JobType.TEST,
            typeStr: JobType.TEST.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.FAILED,
            stateStr: JobState.FAILED.toUpperCase(),
            type: JobType.OPTIMIZATION_POT,
            typeStr: JobType.OPTIMIZATION_POT.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },

        {
            state: JobState.CANCELLED,
            stateStr: JobState.CANCELLED.toUpperCase(),
            type: JobType.TRAIN,
            typeStr: JobType.TRAIN.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.CANCELLED,
            stateStr: JobState.CANCELLED.toUpperCase(),
            type: JobType.TEST,
            typeStr: JobType.TEST.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.CANCELLED,
            stateStr: JobState.CANCELLED.toUpperCase(),
            type: JobType.OPTIMIZATION_POT,
            typeStr: JobType.OPTIMIZATION_POT.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },

        {
            state: JobState.FINISHED,
            stateStr: JobState.FINISHED.toUpperCase(),
            type: JobType.TRAIN,
            typeStr: JobType.TRAIN.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.FINISHED,
            stateStr: JobState.FINISHED.toUpperCase(),
            type: JobType.TEST,
            typeStr: JobType.TEST.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.FINISHED,
            stateStr: JobState.FINISHED.toUpperCase(),
            type: JobType.OPTIMIZATION_POT,
            typeStr: JobType.OPTIMIZATION_POT.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },

        {
            state: JobState.SCHEDULED,
            stateStr: JobState.SCHEDULED.toUpperCase(),
            type: JobType.TRAIN,
            typeStr: JobType.TRAIN.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.SCHEDULED,
            stateStr: JobState.SCHEDULED.toUpperCase(),
            type: JobType.TEST,
            typeStr: JobType.TEST.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
        {
            state: JobState.SCHEDULED,
            stateStr: JobState.SCHEDULED.toUpperCase(),
            type: JobType.OPTIMIZATION_POT,
            typeStr: JobType.OPTIMIZATION_POT.toUpperCase(),
            result: false,
            resultStr: 'not define',
        },
    ])(
        'should $resultStr job as "isRunningTrainingJob" when state is "$stateStr" and job type is "$typeStr"',
        ({ state, type, result }): void => {
            // @ts-expect-error check all types
            expect(isRunningTrainingJob({ ...getMockedJob(), state, type })).toBe(result);
        }
    );

    it('isJobDone', () => {
        expect(isJobDone({ state: JobState.CANCELLED })).toBe(false);
        expect(isJobDone({ state: JobState.FAILED })).toBe(false);
        expect(isJobDone({ state: JobState.RUNNING })).toBe(false);
        expect(isJobDone({ state: JobState.SCHEDULED })).toBe(false);
        expect(isJobDone({ state: JobState.FINISHED })).toBe(true);
    });

    it('isJobCancel', () => {
        expect(isJobCancel({ state: JobState.CANCELLED })).toBe(true);
        expect(isJobCancel({ state: JobState.FAILED })).toBe(false);
        expect(isJobCancel({ state: JobState.RUNNING })).toBe(false);
        expect(isJobCancel({ state: JobState.SCHEDULED })).toBe(false);
        expect(isJobCancel({ state: JobState.FINISHED })).toBe(false);
    });

    it('isJobCancelOrFailed', () => {
        expect(isJobCancelOrFailed({ state: JobState.CANCELLED })).toBe(true);
        expect(isJobCancelOrFailed({ state: JobState.FAILED })).toBe(true);
        expect(isJobCancelOrFailed({ state: JobState.RUNNING })).toBe(false);
        expect(isJobCancelOrFailed({ state: JobState.SCHEDULED })).toBe(false);
        expect(isJobCancelOrFailed({ state: JobState.FINISHED })).toBe(false);
    });

    it('isJobSettled', () => {
        expect(isJobSettled({ state: JobState.CANCELLED })).toBe(true);
        expect(isJobSettled({ state: JobState.FAILED })).toBe(true);
        expect(isJobSettled({ state: JobState.RUNNING })).toBe(false);
        expect(isJobSettled({ state: JobState.SCHEDULED })).toBe(false);
        expect(isJobSettled({ state: JobState.FINISHED })).toBe(true);
    });

    it('isJobExportDone', () => {
        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_DATASET, state: JobState.FINISHED }))).toBe(true);
        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_DATASET, state: JobState.CANCELLED }))).toBe(false);
        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_DATASET, state: JobState.FAILED }))).toBe(false);
        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_DATASET, state: JobState.RUNNING }))).toBe(false);

        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_PROJECT, state: JobState.FINISHED }))).toBe(true);
        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_PROJECT, state: JobState.CANCELLED }))).toBe(false);
        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_PROJECT, state: JobState.FAILED }))).toBe(false);
        expect(isJobExportDone(getMockedJob({ type: JobType.EXPORT_PROJECT, state: JobState.RUNNING }))).toBe(false);
    });
});

describe('formatJobDuration', () => {
    it('formats duration less than a minute correctly', () => {
        expect(formatJobDuration(45)).toBe('45 sec');
    });

    it('formats exactly one minute correctly', () => {
        expect(formatJobDuration(60)).toBe('1 min');
    });

    it('formats duration less than an hour but more than a minute correctly', () => {
        expect(formatJobDuration(75)).toBe('1 min, 15 sec');
    });

    it('formats exactly one hour correctly', () => {
        expect(formatJobDuration(3600)).toBe('1 hr');
    });

    it('formats duration more than an hour correctly', () => {
        expect(formatJobDuration(3665)).toBe('1 hr, 1 min, 5 sec');
    });

    it('formats exactly one day correctly', () => {
        expect(formatJobDuration(86400)).toBe('1 d');
    });

    it('formats duration more than a day correctly', () => {
        expect(formatJobDuration(90061)).toBe('1 d, 1 hr');
    });

    it('formats zero duration correctly', () => {
        expect(formatJobDuration(0)).toBe('0 sec');
    });

    it('handles negative duration gracefully', () => {
        expect(formatJobDuration(-45)).toBe('0 sec');
    });
});

describe('getJobDuration', () => {
    it.each([JobState.FAILED, JobState.RUNNING, JobState.SCHEDULED, JobState.CANCELLED])(
        'returns undefined for unfinished jobs',
        (jobState) => {
            expect(getJobDuration(getMockedJob({ state: jobState }))).toBeUndefined();
        }
    );

    it('returns sum of the durations from each step', () => {
        const job = getMockedJob({
            state: JobState.FINISHED,
            endTime: '2025-02-11T08:50:58.354000+00:00',
            startTime: '2025-02-11T08:48:25.725000+00:00',
            steps: [
                {
                    message: 'Training data prepared',
                    index: 1,
                    progress: 100,
                    state: JobStepState.FINISHED,
                    duration: 11.678,
                    stepName: 'Prepare training data',
                },
                {
                    message: 'Model is trained',
                    index: 2,
                    progress: 100,
                    state: JobStepState.FINISHED,
                    duration: 14.002,
                    stepName: 'Model training',
                },
                {
                    message: 'Model is evaluated and inference is finished',
                    index: 3,
                    progress: 100,
                    state: JobStepState.FINISHED,
                    duration: 22.029,
                    stepName: 'Model evaluation and inference',
                },
            ],
        });

        expect(getJobDuration(job)).toBe('2 min, 32 sec');
    });
});
