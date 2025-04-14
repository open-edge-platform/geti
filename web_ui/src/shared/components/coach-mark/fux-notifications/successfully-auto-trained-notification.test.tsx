// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { GETI_SYSTEM_AUTHOR_ID, JobState, JobType } from '../../../../core/jobs/jobs.const';
import { createInMemoryJobsService } from '../../../../core/jobs/services/in-memory-jobs-service';
import { ModelsGroups } from '../../../../core/models/models.interface';
import { createInMemoryModelsService } from '../../../../core/models/services/in-memory-models-service';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { createInMemoryUserSettingsService } from '../../../../core/user-settings/services/in-memory-user-settings-service';
import { UserGlobalSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { ProjectProvider } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { getMockedJob, getMockedJobCount } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedModelsGroup } from '../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedUserGlobalSettings } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { SuccessfullyAutotrainedNotification } from './successfully-auto-trained-notification.component';

jest.mock('../../../../core/projects/domains', () => ({
    ...jest.requireActual('../../../../core/projects/domains'),
    isAnomalyDomain: jest.fn(),
}));

const mockHandleFirstSuccessfulAutoTraining = jest.fn();
jest.mock('../../../../hooks/use-fux-notifications/use-fux-notifications.hook', () => {
    return {
        useFuxNotifications: jest.fn(() => ({
            handleFirstSuccessfulAutoTraining: mockHandleFirstSuccessfulAutoTraining,
        })),
    };
});

const mockedProjectIdentifier = {
    projectId: 'project-id',
    workspaceId: 'workspace-id',
    organizationId: 'organization-id',
};

describe('Successfully Auto Trained Notification', () => {
    const jobsService = createInMemoryJobsService();
    const modelsService = createInMemoryModelsService();
    const userSettingsService = createInMemoryUserSettingsService();
    const mockedTrainModelId = 'model-id';

    const renderApp = async ({
        trainedModelId,
        models = [],
        customConfig = {},
    }: {
        trainedModelId?: string;
        models?: ModelsGroups[];
        customConfig?: Partial<UserGlobalSettings>;
    }) => {
        jobsService.getJobs = async () => ({
            jobs: [
                getMockedJob({
                    id: 'firstScheduledAutoTrainingJobId',
                    state: JobState.FINISHED,
                    type: JobType.TRAIN,
                    authorId: GETI_SYSTEM_AUTHOR_ID,
                    metadata: {
                        task: {
                            taskId: 'task-id',
                            modelArchitecture: 'YoloV4',
                            name: 'Detection',
                            datasetStorageId: 'dataset-storage-id',
                            modelTemplateId: 'template-id',
                        },
                        project: {
                            id: 'project-id',
                            name: 'example project',
                        },
                        trainedModel: {
                            modelId: trainedModelId,
                        },
                    },
                }),
            ],
            jobsCount: getMockedJobCount({ numberOfFinishedJobs: 1 }),
            nextPage: '',
        });

        modelsService.getModels = jest.fn(async () => models);

        userSettingsService.getGlobalSettings = () =>
            Promise.resolve(
                getMockedUserGlobalSettings({
                    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: 'project-id' },
                    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: { value: 'firstScheduledAutoTrainingJobId' },
                    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: { value: null },
                    [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: { value: true },
                    ...customConfig,
                })
            );

        render(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <SuccessfullyAutotrainedNotification />
            </ProjectProvider>,
            {
                services: { jobsService, modelsService, userSettingsService },
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('will not display the notification and will not fire handleFirstSuccessfulAutoTraining, if anomalous project', async () => {
        jest.mocked(isAnomalyDomain).mockReturnValue(true);

        await renderApp({ trainedModelId: mockedTrainModelId });

        expect(screen.queryByText(/Your model has been successfully trained/)).not.toBeInTheDocument();
        expect(mockHandleFirstSuccessfulAutoTraining).not.toHaveBeenCalled();
    });

    it('will not display the notification and will not fire handleFirstSuccessfulAutoTraining, if the project was previously auto-trained', async () => {
        jest.mocked(isAnomalyDomain).mockReturnValue(false);

        await renderApp({
            trainedModelId: mockedTrainModelId,
            customConfig: { [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: { value: false } },
        });

        expect(screen.queryByText(/Your model has been successfully trained/)).not.toBeInTheDocument();
        expect(mockHandleFirstSuccessfulAutoTraining).not.toHaveBeenCalled();
    });

    it('will not display the notification and will not fire handleFirstSuccessfulAutoTraining, if the trainedModelId is null or undefined', async () => {
        jest.mocked(isAnomalyDomain).mockReturnValue(false);

        await renderApp({ trainedModelId: undefined });

        expect(screen.queryByText(/Your model has been successfully trained/)).not.toBeInTheDocument();
        expect(mockHandleFirstSuccessfulAutoTraining).not.toHaveBeenCalled();
    });

    it('will fire handleFirstSuccessfulAutoTraining only for non-anomalous and never previously auto-trained project and when trainedModelId correctly retrieved', async () => {
        jest.mocked(isAnomalyDomain).mockReturnValue(false);

        await renderApp({ trainedModelId: mockedTrainModelId });

        await waitFor(() => expect(mockHandleFirstSuccessfulAutoTraining).toHaveBeenCalledTimes(1));
    });

    it(`will not display the SuccessfullyAutotrainedNotification if couldn't find the model containing the trainedModelId retrieved from the successfully auto-trained job`, async () => {
        jest.mocked(isAnomalyDomain).mockReturnValue(false);

        await renderApp({
            trainedModelId: mockedTrainModelId,
            customConfig: {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_SUCCESSFULLY_TRAINED]: { isEnabled: true },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: { value: 'model-id' },
            },
        });

        expect(screen.queryByText(/Your model has been successfully trained/)).not.toBeInTheDocument();
    });

    it(`will display the SuccessfullyAutotrainedNotification if firstAutoTrainedModelId is not null the model containing the trainedModelId retrieved from the successfully auto-trained job was found`, async () => {
        jest.mocked(isAnomalyDomain).mockReturnValue(false);

        await renderApp({
            trainedModelId: mockedTrainModelId,
            models: [getMockedModelsGroup()],
            customConfig: {
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_SUCCESSFULLY_TRAINED]: { isEnabled: true },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: { value: 'model-id' },
            },
        });

        expect(await screen.findByText(/Your model has been successfully trained/)).toBeVisible();
    });
});
