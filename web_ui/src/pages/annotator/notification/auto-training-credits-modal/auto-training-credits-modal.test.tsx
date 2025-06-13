// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { BooleanGroupParams } from '../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { JobState } from '../../../../core/jobs/jobs.const';
import { createInMemoryJobsService } from '../../../../core/jobs/services/in-memory-jobs-service';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserGlobalSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { INITIAL_GLOBAL_SETTINGS } from '../../../../core/user-settings/utils';
import { useActiveLearningConfiguration } from '../../../../shared/components/header/active-learning-configuration/use-active-learning-configuration.hook';
import { getFuxSetting } from '../../../../shared/components/tutorials/utils';
import { getMockedJob, getMockedJobCount } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import {
    getMockedUserGlobalSettings,
    getMockedUserGlobalSettingsObject,
} from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { AutoTrainingCreditsModal } from './auto-training-credits-modal.component';

jest.mock('./util', () => ({
    ...jest.requireActual('./util'),
    onFirstScheduledOrRunningAutoTrainingJob:
        (_settings: UseSettings<UserGlobalSettings>, callback: () => void) => () =>
            callback(),
}));

jest.mock(
    '../../../../shared/components/header/active-learning-configuration/use-active-learning-configuration.hook',
    () => ({
        ...jest.requireActual(
            '../../../../shared/components/header/active-learning-configuration/use-active-learning-configuration.hook'
        ),
        useActiveLearningConfiguration: jest.fn(),
    })
);

jest.mock('../../../../shared/components/tutorials/utils', () => ({
    getFuxSetting: jest.fn(),
}));

const mockedProjectIdentifier = {
    projectId: 'project-id',
    workspaceId: 'workspace-id',
    organizationId: 'organization-id',
};

const getMockedAutoTraining = (value: boolean) =>
    ({
        id: '123::321',
        header: 'Auto-training',
        value,
    }) as BooleanGroupParams;

describe('AutoTrainingCreditsModal', () => {
    const renderApp = async ({
        settings = {},
        mockedSaveSettings = jest.fn(),
        isTrainingConfigOn = true,
        isLoadingAutoTrainingConfig = false,
    }: {
        mockedSaveSettings?: jest.Mock;
        settings?: Partial<UserGlobalSettings>;
        isLoadingAutoTrainingConfig?: boolean;
        isTrainingConfigOn?: boolean;
    }) => {
        const getJobsService = jest.fn();
        const jobsService = createInMemoryJobsService();

        jest.mocked(useActiveLearningConfiguration).mockReturnValue({
            isPending: isLoadingAutoTrainingConfig,
            autoTrainingTasks: [{ task: getMockedTask({}), trainingConfig: getMockedAutoTraining(isTrainingConfigOn) }],
            updateDynamicRequiredAnnotations: jest.fn(),
            updateAutoTraining: jest.fn(),
            updateRequiredImagesAutoTraining: jest.fn(),
        });

        jobsService.getJobs = getJobsService.mockResolvedValue({
            jobs: [
                getMockedJob({
                    state: JobState.SCHEDULED,
                    cost: { requests: [{ amount: 10, unit: 'images' }], leaseId: '123', consumed: [] },
                }),
            ],
            jobsCount: getMockedJobCount({}),
            nextPage: '',
        });

        render(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <TaskProvider>
                    <AutoTrainingCreditsModal
                        settings={getMockedUserGlobalSettingsObject({
                            saveConfig: mockedSaveSettings,
                            config: getMockedUserGlobalSettings(settings),
                        })}
                    />
                </TaskProvider>
            </ProjectProvider>,
            { services: { jobsService } }
        );

        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));

        return { getJobsService };
    };

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('modal is open and disabled by dismissing', async () => {
        const mockedSaveSettings = jest.fn();
        jest.mocked(getFuxSetting).mockReturnValue(true);

        await renderApp({ mockedSaveSettings });

        const dismissButton = await screen.findByRole('button', { name: /dismiss/i });
        await waitFor(() => expect(dismissButton).toBeVisible());

        fireEvent.click(dismissButton);

        await waitFor(() => expect(screen.queryByRole('button', { name: /dismiss/i })).not.toBeInTheDocument());

        expect(mockedSaveSettings).toHaveBeenCalledWith({
            ...INITIAL_GLOBAL_SETTINGS,
            [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: false },
            [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: { isEnabled: true },
            [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: 'project-id' },
        });
    });

    describe('modal is enabled', () => {
        it('settings: AUTO_TRAINING_MODAL is undefined', async () => {
            const { getJobsService } = await renderApp({ settings: { autoTrainingCreditModal: undefined } });

            expect(getJobsService).toHaveBeenCalled();
        });

        it('settings: AUTO_TRAINING_MODAL is true', async () => {
            const { getJobsService } = await renderApp({ settings: { autoTrainingCreditModal: { isEnabled: true } } });

            expect(getJobsService).toHaveBeenCalled();
        });
    });

    describe('modal is disabled', () => {
        it('AutoTrainingTasksConfig is off', async () => {
            const { getJobsService } = await renderApp({ isTrainingConfigOn: false });

            expect(getJobsService).not.toHaveBeenCalled();
        });

        it('it is loading AutoTrainingConfig', async () => {
            const { getJobsService } = await renderApp({ isLoadingAutoTrainingConfig: true });

            expect(getJobsService).not.toHaveBeenCalled();
        });
    });
});
