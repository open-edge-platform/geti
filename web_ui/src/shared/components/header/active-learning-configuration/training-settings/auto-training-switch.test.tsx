// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import {
    BooleanGroupParams,
    NumberGroupParams,
} from '../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { JobState } from '../../../../../core/jobs/jobs.const';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { PerformanceType } from '../../../../../core/projects/task.interface';
import { LifecycleStage } from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedModelVersion } from '../../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { getAllJobs } from '../../jobs-management/utils';
import { AutoTrainingSwitch } from './auto-training-switch.component';

const mockInvalidateQueries = jest.fn();
jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }),
}));

jest.mock('../../../../../core/jobs/hooks/use-jobs.hook', () => ({
    useGetRunningJobs: jest.fn(() => ({
        pages: [{ data: [] }],
    })),
    useJobs: jest.fn(() => ({
        useDeleteJob: jest.fn(),
        useCancelJob: jest.fn(),
    })),
}));

jest.mock('../../jobs-management/utils', () => ({
    ...jest.requireActual('../../jobs-management/utils'),
    getAllJobs: jest.fn(() => []),
}));

jest.mock('../../../../utils', () => ({
    ...jest.requireActual('../../../../utils'),
    openNewTab: jest.fn(),
}));

describe('AutoTrainingSwitch', () => {
    const projectIdentifier = getMockedProjectIdentifier({ projectId: '123321', workspaceId: '324' });
    const task = getMockedTask({ title: 'detection', id: 'detection', domain: DOMAIN.DETECTION });
    const mockAutoTrainingEnabled = { id: '123::321', header: 'Auto-training', value: true } as BooleanGroupParams;
    const adaptiveRequiredAnnotationsEnabled = {
        id: '123::321',
        header: 'Use adaptive auto-training threshold',
        value: true,
    } as BooleanGroupParams;
    const adaptiveRequiredAnnotationsNotEnabled = {
        id: '123::321',
        header: 'Use adaptive auto-training threshold',
        value: false,
    } as BooleanGroupParams;
    const mockRequiredAnnotationsConfig = {
        id: '672218cc1cd7265d334f5236::672218cc055da73fae28e7e6::1f94ce5d-0194-44b1-b118-a965a10fa038',
        header: 'Number of images required for auto-training',
        value: 12,
        minValue: 3,
        maxValue: 10000,
    } as NumberGroupParams;
    const mockModel: ModelsGroups = {
        taskId: '649c6f6cc7bf707395ca76db',
        groupId: '649d8910272a022ea4686875',
        modelSummary: 'Class-Incremental Image Classification for MobileNet-V3-large-1x',
        groupName: 'MobileNet-V3-large-1x',
        modelVersions: [
            getMockedModelVersion({
                version: 1,
                performance: {
                    score: 0.6923076923076923,
                    type: PerformanceType.DEFAULT,
                },
                groupName: 'MobileNet-V3-large-1x',
                id: '649d896b80a5912dfcad0b9f',
                groupId: '649d8910272a022ea4686875',
                isActiveModel: true,
                creationDate: '2023-06-29T13:38:51.242000+00:00',
                templateName: 'Speed',
                isLabelSchemaUpToDate: true,
            }),
        ],
        modelTemplateName: 'Speed',
        modelTemplateId: 'Custom_Image_Classification_MobileNet-V3-large-1x',
        lifecycleStage: LifecycleStage.ACTIVE,
    };

    const getAutoTrainingSwitch = () => screen.getByRole('switch', { name: `Toggle auto training for ${task.title}` });

    const getAutoTrainingThreshold = () => screen.queryByText('Auto-training threshold');
    const getAdaptiveThreshold = () => screen.getByRole('radio', { name: /adaptive/i });
    const getFixedThreshold = () => screen.getByRole('radio', { name: /fixed/i });
    const getNumberOfRequiredAnnotationsSlider = () =>
        screen.getByRole('slider', { name: 'Number of required annotations' });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('does not display active model info when there is no active model', async () => {
        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={undefined}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        expect(screen.queryByRole('link', { name: /active model link/i })).not.toBeInTheDocument();
    });

    it('display active model info when there is active model', async () => {
        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        const [activeVersion] = mockModel.modelVersions;
        const link = screen.getByRole('link', { name: /active model link/i });

        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute(
            'href',
            `/organizations/${projectIdentifier.organizationId}/workspaces/${projectIdentifier.workspaceId}/projects/${projectIdentifier.projectId}/models/${mockModel.groupId}/${activeVersion.id}/model-variants`
        );
    });

    it('toggling auto training updates the configurable parameters', async () => {
        const mockUpdateAutoTraining = jest.fn();

        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={mockUpdateAutoTraining}
            />
        );

        fireEvent.click(getAutoTrainingSwitch());

        await waitFor(() => {
            expect(mockUpdateAutoTraining).toHaveBeenCalledWith(false);
        });
    });

    it('auto training threshold is not available when auto training is not enabled', async () => {
        const autoTrainingNotEnabled = { ...mockAutoTrainingEnabled, value: false } as BooleanGroupParams;

        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={autoTrainingNotEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                requiredImagesAutoTrainingConfig={mockRequiredAnnotationsConfig}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        expect(getAutoTrainingSwitch()).not.toBeChecked();
        expect(getAutoTrainingThreshold()).not.toBeInTheDocument();
    });

    it('auto training threshold is available only when auto training is enabled', async () => {
        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                requiredImagesAutoTrainingConfig={mockRequiredAnnotationsConfig}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        expect(getAutoTrainingSwitch()).toBeChecked();
        expect(getAutoTrainingThreshold()).toBeInTheDocument();
        expect(getAdaptiveThreshold()).toBeInTheDocument();
        expect(getFixedThreshold()).toBeInTheDocument();
    });

    it('selecting auto training threshold updates the configurable parameters', async () => {
        const mockUpdateDynamicRequiredAnnotations = jest.fn();

        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                requiredImagesAutoTrainingConfig={mockRequiredAnnotationsConfig}
                onUpdateDynamicRequiredAnnotations={mockUpdateDynamicRequiredAnnotations}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        const fixedThreshold = getFixedThreshold();

        expect(getAdaptiveThreshold()).toBeChecked();
        expect(fixedThreshold).not.toBeChecked();

        fireEvent.click(fixedThreshold);

        await waitFor(() => {
            expect(mockUpdateDynamicRequiredAnnotations).toHaveBeenCalledWith(false);
        });
    });

    it('when "Adaptive" threshold is selected, user is not allowed to change number of required annotations', async () => {
        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                requiredImagesAutoTrainingConfig={mockRequiredAnnotationsConfig}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        expect(getAdaptiveThreshold()).toBeChecked();
        expect(getFixedThreshold()).not.toBeChecked();
    });

    it('when "Fixed" threshold is selected, user is allowed to change number of required annotations', async () => {
        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsNotEnabled}
                requiredImagesAutoTrainingConfig={mockRequiredAnnotationsConfig}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        expect(getFixedThreshold()).toBeChecked();
        expect(getAdaptiveThreshold()).not.toBeChecked();
        expect(getNumberOfRequiredAnnotationsSlider()).toBeInTheDocument();
    });

    it('changes required images annotations config', async () => {
        const mockUpdateRequiredImagesAutoTraining = jest.fn();

        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                activeModel={mockModel}
                task={task}
                projectIdentifier={projectIdentifier}
                trainingConfig={mockAutoTrainingEnabled}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsNotEnabled}
                requiredImagesAutoTrainingConfig={mockRequiredAnnotationsConfig}
                onUpdateRequiredImagesAutoTraining={mockUpdateRequiredImagesAutoTraining}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateAutoTraining={jest.fn()}
            />
        );

        const slider = getNumberOfRequiredAnnotationsSlider();
        fireEvent.keyDown(slider, { key: 'Right' });

        await waitFor(() => {
            expect(mockUpdateRequiredImagesAutoTraining).toHaveBeenCalledWith(mockRequiredAnnotationsConfig.value + 1);
        });
    });

    it('auto training switch is disabled with running task', async () => {
        const mockedJobs = [
            {
                state: JobState.RUNNING,
                metadata: {
                    project: { id: '123321' },
                    task: {
                        taskId: task.id,
                        name: 'detection',
                    },
                },
            },
        ];

        // @ts-expect-error We only care about mocking metadata
        jest.mocked(getAllJobs).mockReturnValue(mockedJobs);

        await render(
            <AutoTrainingSwitch
                isTaskChainMode={false}
                task={task}
                activeModel={mockModel}
                projectIdentifier={projectIdentifier}
                trainingConfig={{ ...mockAutoTrainingEnabled, value: false }}
                dynamicRequiredAnnotationsConfig={adaptiveRequiredAnnotationsEnabled}
                onUpdateAutoTraining={jest.fn()}
                onUpdateDynamicRequiredAnnotations={jest.fn()}
                onUpdateRequiredImagesAutoTraining={jest.fn()}
            />
        );

        const autoTrainingSwitch = getAutoTrainingSwitch();

        expect(autoTrainingSwitch).toBeVisible();
        expect(autoTrainingSwitch).toBeDisabled();
    });
});
