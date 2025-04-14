// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { GETI_SYSTEM_AUTHOR_ID, JobState } from '../../../../core/jobs/jobs.const';
import { Job, JobCount } from '../../../../core/jobs/jobs.interface';
import { getFuxSetting } from '../../../../shared/components/tutorials/utils';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedUserGlobalSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { onFirstScheduledAutoTrainingJob } from './util';

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

    describe('onFirstScheduledAutoTrainingJob', () => {
        const mockedCallback = jest.fn();

        it('invalid response', () => {
            onFirstScheduledAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )({ pageParams: [undefined], pages: [] });
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('it is first scheduled autotraining job', () => {
            jest.mocked(getFuxSetting).mockReturnValue(true);
            onFirstScheduledAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )(
                getJobResponse({ numberOfScheduledJobs: 1 }, [
                    getMockedJob({ state: JobState.SCHEDULED, authorId: GETI_SYSTEM_AUTHOR_ID }),
                ])
            );

            expect(mockedCallback).toBeCalledTimes(1);
        });

        it('it is scheduled job but user has previously autotrained', () => {
            jest.mocked(getFuxSetting).mockReturnValue(false);
            onFirstScheduledAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )(getJobResponse({ numberOfScheduledJobs: 1 }));

            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('it is first manually scheduled training job', () => {
            onFirstScheduledAutoTrainingJob(
                getMockedUserGlobalSettingsObject(),
                mockedCallback
            )(
                getJobResponse({ numberOfScheduledJobs: 1 }, [
                    getMockedJob({ state: JobState.SCHEDULED, authorId: 'user-id' }),
                ])
            );
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('no scheduled jobs', () => {
            jest.mocked(getFuxSetting).mockReturnValue(true);
            onFirstScheduledAutoTrainingJob(getMockedUserGlobalSettingsObject(), mockedCallback)(getJobResponse());
            expect(mockedCallback).toBeCalledTimes(0);
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
                onFirstScheduledAutoTrainingJob(
                    getMockedUserGlobalSettingsObject(),
                    mockedCallback
                )(
                    getJobResponse({ numberOfScheduledJobs: 1, [jobName]: 1 }, [
                        getMockedJob({ state: JobState.SCHEDULED, authorId: GETI_SYSTEM_AUTHOR_ID }),
                    ])
                );
                expect(mockedCallback).toBeCalledTimes(1);
            });
        });
    });
});
