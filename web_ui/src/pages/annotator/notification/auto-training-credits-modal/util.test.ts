// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { GETI_SYSTEM_AUTHOR_ID, JobState } from '../../../../core/jobs/jobs.const';
import { Job, JobCount } from '../../../../core/jobs/jobs.interface';
import { getFuxSetting } from '../../../../shared/components/tutorials/utils';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedUserGlobalSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { onFirstScheduledOrRunningAutoTrainingJob } from './util';

const getJobResponse = (jobCount: Partial<JobCount> = {}, mockedJobs: Job[] = []) => ({
    pageParams: [undefined],
    pages: [
        {
            jobs: mockedJobs,
            nextPage: undefined,
            jobsCount: {
                numberOfRunningJobs: 0,
                numberOfFinishedJobs: 0,
                numberOfScheduledJobs: 0,
                numberOfCancelledJobs: 0,
                numberOfFailedJobs: 0,
                ...jobCount,
            },
        },
    ],
});

jest.mock('../../../../shared/components/tutorials/utils', () => ({
    getFuxSetting: jest.fn(),
}));

describe('auto-training-credits-modal utils', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('onFirstScheduledOrRunningAutoTrainingJob', () => {
        const mockedCallback = jest.fn();

        it('invalid response', () => {
            onFirstScheduledOrRunningAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )({ pageParams: [undefined], pages: [] });
            expect(mockedCallback).toHaveBeenCalledTimes(0);
        });

        it('it is first scheduled auto-training job', () => {
            jest.mocked(getFuxSetting).mockReturnValue(true);
            onFirstScheduledOrRunningAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )(
                getJobResponse({ numberOfScheduledJobs: 1 }, [
                    getMockedJob({ state: JobState.SCHEDULED, authorId: GETI_SYSTEM_AUTHOR_ID }),
                ])
            );

            expect(mockedCallback).toHaveBeenCalledTimes(1);
        });

        it('it is first running auto-training job', () => {
            jest.mocked(getFuxSetting).mockReturnValue(true);
            onFirstScheduledOrRunningAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )(
                getJobResponse({ numberOfScheduledJobs: 1 }, [
                    getMockedJob({ state: JobState.RUNNING, authorId: GETI_SYSTEM_AUTHOR_ID }),
                ])
            );

            expect(mockedCallback).toHaveBeenCalledTimes(1);
        });

        it('it is scheduled job but user has previously auto-trained', () => {
            jest.mocked(getFuxSetting).mockReturnValue(false);
            onFirstScheduledOrRunningAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )(getJobResponse({ numberOfScheduledJobs: 1 }));

            expect(mockedCallback).toHaveBeenCalledTimes(0);
        });

        it('it is first manually scheduled training job', () => {
            onFirstScheduledOrRunningAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )(
                getJobResponse({ numberOfScheduledJobs: 1 }, [
                    getMockedJob({ state: JobState.SCHEDULED, authorId: 'user-id' }),
                ])
            );
            expect(mockedCallback).toHaveBeenCalledTimes(0);
        });

        it('no scheduled jobs', () => {
            jest.mocked(getFuxSetting).mockReturnValue(true);
            onFirstScheduledOrRunningAutoTrainingJob(getMockedUserGlobalSettingsObject(), mockedCallback)(getJobResponse());
            expect(mockedCallback).toHaveBeenCalledTimes(0);
        });

        describe('it is not the first job', () => {
            const testData: [string][] = [
                ['numberOfRunningJobs'],
                ['numberOfFinishedJobs'],
                ['numberOfCancelledJobs'],
                ['numberOfFailedJobs'],
            ];
            jest.mocked(getFuxSetting).mockReturnValue(true);
            test.each(testData)('%s', (jobName) => {
                onFirstScheduledOrRunningAutoTrainingJob(
                    getMockedUserGlobalSettingsObject(),
                    mockedCallback
                )(
                    getJobResponse({ numberOfScheduledJobs: 1, [jobName]: 1 }, [
                        getMockedJob({ state: JobState.SCHEDULED, authorId: GETI_SYSTEM_AUTHOR_ID }),
                    ])
                );
                expect(mockedCallback).toHaveBeenCalledTimes(1);
            });
        });
    });
});
