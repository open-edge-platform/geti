// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, RenderResult, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryModelsService } from '../../../../../core/models/services/in-memory-models-service';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { createInMemorySupportedAlgorithmsService } from '../../../../../core/supported-algorithms/services/in-memory-supported-algorithms-service';
import { getMockedSupportedAlgorithm } from '../../../../../core/supported-algorithms/services/test-utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import {
    getMockedModelsGroup,
    getMockedModelVersion,
} from '../../../../../test-utils/mocked-items-factory/mocked-model';
import {
    getMockedProject,
    getMockedProjectStatus,
    getMockedProjectStatusTask,
} from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { Template } from './model-templates-selection/model-templates-list/model-templates-list.interface';
import { ModelConfigurationOption } from './model-templates-selection/utils';
import { TrainModelDialog } from './train-model-dialog.component';
import { getModelTemplates, TRAIN_FROM_SCRATCH_TOOLTIP_MSG } from './utils';

describe('Train model dialog', () => {
    const taskId = '1';
    const projectIdMocked = 'project-id';

    const mockedSingleTaskProject = getMockedProject({
        id: projectIdMocked,
        tasks: [{ id: taskId, domain: DOMAIN.DETECTION, labels: [], title: DOMAIN.DETECTION }],
        labels: [],
        datasets: [{ id: 'dataset-id', name: 'test dataset', creationTime: '', useForTraining: true }],
    });

    const supportedAlgorithmsService = createInMemorySupportedAlgorithmsService();
    const modelsService = createInMemoryModelsService();

    const selectedClass = 'selectableCard selectableCardSelected';

    const mockedSupportedAlgorithmsForDetection = [
        getMockedSupportedAlgorithm({
            name: 'YOLO',
            domain: DOMAIN.DETECTION,
            modelSize: 200,
            modelTemplateId: 'detection_yolo',
            gigaflops: 1.3,
            summary: 'YOLO architecture for detection',
            isDefaultAlgorithm: true,
        }),
        getMockedSupportedAlgorithm({
            name: 'SSD',
            domain: DOMAIN.DETECTION,
            modelSize: 100,
            modelTemplateId: 'detection_ssd',
            gigaflops: 5.4,
            summary: 'SSD architecture for detection',
            isDefaultAlgorithm: false,
        }),
        getMockedSupportedAlgorithm({
            name: 'ATTS',
            domain: DOMAIN.DETECTION,
            modelSize: 150,
            modelTemplateId: 'detection_atts',
            gigaflops: 3,
            summary: 'ATTS architecture for detection',
            isDefaultAlgorithm: false,
        }),
    ];

    supportedAlgorithmsService.getProjectSupportedAlgorithms = jest.fn(
        async () => mockedSupportedAlgorithmsForDetection
    );

    const mockedModels = [getMockedModelsGroup()];

    const defaultAlgorithm = mockedSupportedAlgorithmsForDetection.find(({ isDefaultAlgorithm }) => isDefaultAlgorithm);
    const templates = getModelTemplates(mockedSupportedAlgorithmsForDetection);

    const goToConfigureParametersStep = async () => {
        fireEvent.click(await screen.findByRole('radio', { name: ModelConfigurationOption.MANUAL_CONFIGURATION }));
        fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    };

    const renderTrainModelDialog = async (props?: {
        projectId?: string;
        options?: Parameters<typeof render>['1'];
        onClose?: jest.Mock;
        onSuccess?: jest.Mock;
    }): Promise<RenderResult> => {
        const { options = {}, onClose = jest.fn(), onSuccess = jest.fn() } = props ?? {};
        const projectService = createInMemoryProjectService();

        projectService.getProject = jest.fn(async () => mockedSingleTaskProject);

        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({
                    tasks: [
                        getMockedProjectStatusTask({
                            id: taskId,
                            ready_to_train: true,
                        }),
                    ],
                })
            );

        return await render(<TrainModelDialog isOpen={true} onClose={onClose} onSuccess={onSuccess} />, {
            ...options,
            services: { ...options.services, projectService: options.services?.projectService ?? projectService },
            featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: false },
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('Template with default algorithm should be selected by default if there are no models', async () => {
        modelsService.getModels = jest.fn(async () => []);

        // speed
        const defaultModelTemplate = templates.find(
            ({ modelTemplateId }) => modelTemplateId === defaultAlgorithm?.modelTemplateId
        ) as Template;

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        const defaultTemplateElement = await screen.findByTestId(`${defaultModelTemplate.name.toLocaleLowerCase()}-id`);

        expect(defaultTemplateElement).toHaveClass(selectedClass, { exact: false });
        expect(screen.queryByTestId('selected-inactive-model-id')).not.toBeInTheDocument();
    });

    it('Template which has active model should be selected by default when there are models', async () => {
        const notDefaultAlgorithm = mockedSupportedAlgorithmsForDetection[1];

        const defaultModelTemplate = templates.find(
            ({ modelTemplateId }) => modelTemplateId === notDefaultAlgorithm?.modelTemplateId
        ) as Template;

        modelsService.getModels = jest.fn(async () => [
            getMockedModelsGroup({
                taskId,
                modelTemplateId: defaultModelTemplate.modelTemplateId,
                modelTemplateName: defaultModelTemplate.text,
                modelVersions: [getMockedModelVersion({ isActiveModel: true })],
            }),
        ]);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        // accuracy
        const defaultTemplateElement = await screen.findByTestId(`${defaultModelTemplate.name.toLocaleLowerCase()}-id`);

        expect(defaultTemplateElement).toHaveClass(selectedClass, { exact: false });
        expect(screen.queryByTestId('selected-inactive-model-id')).not.toBeInTheDocument();
    });

    it('Start button is displayed in the selection templates step when latest configuration is selected', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        expect(await screen.findByRole('radio', { name: ModelConfigurationOption.LATEST_CONFIGURATION })).toBeChecked();
        expect(screen.getByRole('radio', { name: ModelConfigurationOption.MANUAL_CONFIGURATION })).not.toBeChecked();

        expect(screen.getByRole('button', { name: 'Start' })).toBeEnabled();
        expect(screen.queryByRole('button', { name: 'Next' })).not.toBeInTheDocument();
    });

    it('submits model and calls onSuccess', async () => {
        const onSuccess = jest.fn();
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            onSuccess,
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        fireEvent.click(await screen.findByRole('button', { name: 'Start' }));

        await waitFor(() => {
            expect(onSuccess).toHaveBeenCalled();
        });
    });

    it('Next button is displayed in the selection templates step when manual configuration is selected', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        const manualConfig = await screen.findByRole('radio', { name: ModelConfigurationOption.MANUAL_CONFIGURATION });

        fireEvent.click(manualConfig);

        expect(manualConfig).toBeChecked();
        expect(screen.getByRole('radio', { name: ModelConfigurationOption.LATEST_CONFIGURATION })).not.toBeChecked();
        expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Start' })).not.toBeInTheDocument();
    });

    it('Back button is not displayed in the selection templates step', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        expect(screen.queryByRole('button', { name: 'Back' })).not.toBeInTheDocument();
    });

    it('Back button is displayed in the selection templates steps', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        await goToConfigureParametersStep();

        expect(screen.getByRole('button', { name: 'Back' })).toBeInTheDocument();
    });

    it('Configuring parameters should be the second step of the training', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        await goToConfigureParametersStep();

        expect(screen.getByText('Configure parameters')).toBeInTheDocument();
    });

    it('Start button should be enabled in the final step of advanced training', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        await goToConfigureParametersStep();

        expect(screen.queryByRole('button', { name: 'Next' })).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Start' })).toBeEnabled();
    });

    it('Training from scratch is only available in the configuring parameters step', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        await goToConfigureParametersStep();

        await waitForElementToBeRemoved(screen.getByTestId('config-params-placeholder-id'));
        expect(screen.getByText('Train from scratch')).toBeInTheDocument();

        fireEvent.click(screen.getByTestId('train-from-scratch-tooltip-id'));

        expect(await screen.findByRole('dialog')).toHaveTextContent(TRAIN_FROM_SCRATCH_TOOLTIP_MSG);
    });

    it('Choices from the previous steps should be remembered', async () => {
        const [, secondAlgorithm] = mockedSupportedAlgorithmsForDetection;

        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        const secondAlgorithmCard = await screen.findByTestId(`${idMatchingFormat(secondAlgorithm.name)}-id`);

        expect(secondAlgorithmCard).not.toHaveClass(selectedClass, { exact: false });
        fireEvent.click(secondAlgorithmCard);
        expect(secondAlgorithmCard).toHaveClass(selectedClass, { exact: false });

        await goToConfigureParametersStep();

        fireEvent.click(screen.getByRole('button', { name: 'Back' }));

        await goToConfigureParametersStep();

        expect(secondAlgorithmCard).toHaveClass(selectedClass, { exact: false });
    });

    it('should select active template by default and open ALL mode when active template comes from not recommended templates', async () => {
        modelsService.getModels = jest.fn(async () => [
            getMockedModelsGroup({
                taskId,
                modelTemplateId: mockedSupportedAlgorithmsForDetection[0].modelTemplateId,
                modelTemplateName: mockedSupportedAlgorithmsForDetection[0].name,
                modelVersions: [getMockedModelVersion({ isActiveModel: true })],
            }),
        ]);

        const supportedAlgorithms = mockedSupportedAlgorithmsForDetection;

        supportedAlgorithmsService.getProjectSupportedAlgorithms = jest.fn(async () => supportedAlgorithms);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        expect(
            await screen.findByTestId(
                `active-model-${idMatchingFormat(mockedSupportedAlgorithmsForDetection[0].name)}-id`
            )
        ).toBeInTheDocument();
    });

    it('unselecting train from scratch should unselect reshuffle option as well', async () => {
        modelsService.getModels = jest.fn(async () => mockedModels);

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService } },
        });

        await goToConfigureParametersStep();

        await waitForElementToBeRemoved(screen.getByTestId('config-params-placeholder-id'));

        fireEvent.click(screen.getByRole('checkbox', { name: 'Train from scratch' }));

        expect(screen.getByRole('checkbox', { name: 'Train from scratch' })).toBeChecked();

        fireEvent.click(screen.getByRole('checkbox', { name: 'Reshuffle subsets' }));

        expect(screen.getByRole('checkbox', { name: 'Reshuffle subsets' })).toBeChecked();

        fireEvent.click(screen.getByRole('checkbox', { name: 'Train from scratch' }));

        expect(screen.getByRole('checkbox', { name: 'Train from scratch' })).not.toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Reshuffle subsets' })).not.toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Reshuffle subsets' })).toBeDisabled();
    });

    it('shows not enough credits when training for the task is not allowed yet', async () => {
        const projectService = createInMemoryProjectService();

        projectService.getProject = jest.fn(async () => mockedSingleTaskProject);
        projectService.getProjectStatus = () =>
            Promise.resolve(
                getMockedProjectStatus({
                    tasks: [
                        getMockedProjectStatusTask({
                            id: taskId,
                            ready_to_train: false,
                        }),
                    ],
                })
            );

        await renderTrainModelDialog({
            options: { services: { supportedAlgorithmsService, modelsService, projectService } },
        });

        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Not enough annotations' })).toBeInTheDocument();
    });
});
