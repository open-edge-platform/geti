// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { GETI_SYSTEM_AUTHOR_ID, JobState } from '../../../core/jobs/jobs.const';
import { Job, JobCount } from '../../../core/jobs/jobs.interface';
import { FUX_SETTINGS_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { getMockedJob } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedUserGlobalSettingsObject } from '../../../test-utils/mocked-items-factory/mocked-settings';
import { getFuxSetting } from '../tutorials/utils';
import { onFirstSuccessfulAutoTrainingJob } from './utils';

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

jest.mock('../tutorials/utils', () => ({
    getFuxSetting: jest.fn(),
}));

describe('CoachMark utils', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('onFirstSuccessfulAutoTrainingJob', () => {
        const mockedCallback = jest.fn();

        it('will not call callback when invalid response', () => {
            onFirstSuccessfulAutoTrainingJob(
                getMockedUserGlobalSettingsObject({}),
                mockedCallback
            )({ pageParams: [undefined], pages: [] });
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('will not call callback when no finished jobs', () => {
            onFirstSuccessfulAutoTrainingJob(getMockedUserGlobalSettingsObject({}), mockedCallback)(getJobResponse());
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('will not call callback when previously autotrained', () => {
            jest.mocked(getFuxSetting).mockImplementationOnce((setting) => {
                if (setting === FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED) {
                    return false;
                } else {
                    return true;
                }
            });
            onFirstSuccessfulAutoTrainingJob(getMockedUserGlobalSettingsObject({}), mockedCallback)(getJobResponse());
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('will not call callback when first scheduled autotraining job id doesnt match finished job id', () => {
            jest.mocked(getFuxSetting).mockImplementationOnce((setting) => {
                if (setting === FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID) {
                    return 'random-job-id';
                } else {
                    return true;
                }
            });
            onFirstSuccessfulAutoTrainingJob(getMockedUserGlobalSettingsObject({}), mockedCallback)(getJobResponse());
            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('will not call callback when first scheduled job id was not autotrained', () => {
            jest.mocked(getFuxSetting).mockImplementation((setting) => {
                if (setting === FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID) {
                    return 'first-autotrained-job-id';
                } else {
                    return true;
                }
            });
            onFirstSuccessfulAutoTrainingJob(
                getMockedUserGlobalSettingsObject({}),
                mockedCallback
            )(
                getJobResponse({ numberOfFinishedJobs: 1 }, [
                    getMockedJob({
                        id: 'first-autotrained-job-id',
                        state: JobState.FINISHED,
                        authorId: 'Kasia',
                    }),
                ])
            );

            expect(mockedCallback).toBeCalledTimes(0);
        });

        it('will call callback ', () => {
            onFirstSuccessfulAutoTrainingJob(
                getMockedUserGlobalSettingsObject({}),
                mockedCallback
            )(
                getJobResponse({ numberOfFinishedJobs: 1 }, [
                    getMockedJob({
                        id: 'first-autotrained-job-id',
                        state: JobState.FINISHED,
                        authorId: GETI_SYSTEM_AUTHOR_ID,
                    }),
                ])
            );

            expect(mockedCallback).toBeCalledTimes(1);
        });
    });
});
