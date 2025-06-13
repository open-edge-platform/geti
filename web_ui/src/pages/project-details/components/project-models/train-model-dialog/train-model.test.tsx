// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { CreditsService } from '../../../../../core/credits/services/credits-service.interface';
import { createInMemoryCreditsService } from '../../../../../core/credits/services/in-memory-credits-service';
import { ModelGroupsAlgorithmDetails } from '../../../../../core/models/models.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../../core/projects/services/project-service.interface';
import {
    LifecycleStage,
    PerformanceCategory,
} from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { getMockedModelsGroup } from '../../../../../test-utils/mocked-items-factory/mocked-model';
import {
    getMockedProjectStatus,
    getMockedProjectStatusTask,
} from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { useTotalCreditPrice } from '../../../hooks/use-credits-to-consume.hook';
import { TrainModel } from './train-model.component';

const mockedUseNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedUseNavigate,
}));

jest.mock('../../../hooks/use-credits-to-consume.hook', () => ({
    useTotalCreditPrice: jest.fn(() => ({
        getCreditPrice: () => ({ totalCreditsToConsume: null, totalMedias: null }),
        isLoading: false,
    })),
}));

const getMockedModelGroupsAlgorithmDetails = (lifecycleStage = LifecycleStage.ACTIVE): ModelGroupsAlgorithmDetails => {
    return {
        ...getMockedModelsGroup(),
        lifecycleStage,
        isDefaultAlgorithm: true,
        performanceCategory: PerformanceCategory.ACCURACY,
        complexity: null,
    };
};

describe('Train model', () => {
    const renderTrainModel = ({
        models,
        projectService = createInMemoryProjectService(),
        creditsService = createInMemoryCreditsService(),
        FEATURE_FLAG_CREDIT_SYSTEM,
        FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS,
    }: {
        models: ModelGroupsAlgorithmDetails[];
        projectService?: ProjectService;
        creditsService?: CreditsService;
        FEATURE_FLAG_CREDIT_SYSTEM?: boolean;
        FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: boolean;
    }) => {
        return render(<TrainModel models={models} />, {
            services: { projectService, creditsService },
            featureFlags: {
                FEATURE_FLAG_CREDIT_SYSTEM,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS,
            },
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('when FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS is enabled', () => {
        it('render "Train new model"', async () => {
            await renderTrainModel({ models: [], FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false });

            expect(screen.getByRole('button', { name: 'Train new model' })).toBeVisible();
        });

        it('render "Train model"', async () => {
            await renderTrainModel({
                models: [getMockedModelGroupsAlgorithmDetails()],
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
            });

            expect(screen.getByRole('button', { name: 'Train model' })).toBeVisible();
        });

        it('open/close modal when training is allowed and FEATURE_FLAG_CREDIT_SYSTEM not enabled', async () => {
            const projectService = createInMemoryProjectService();
            projectService.getProjectStatus = () =>
                Promise.resolve(
                    getMockedProjectStatus({
                        tasks: [getMockedProjectStatusTask({ ready_to_train: true })],
                    })
                );

            await renderTrainModel({
                models: [],
                projectService,
                FEATURE_FLAG_CREDIT_SYSTEM: false,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
            });

            fireEvent.click(screen.getByRole('button', { name: 'Train new model' }));

            expect(screen.getByRole('dialog')).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

            await waitFor(() => {
                expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            });
        });

        it('shows not enough annotations when training is not allowed and FEATURE_FLAG_CREDIT_SYSTEM is not enabled', async () => {
            const projectService = createInMemoryProjectService();
            projectService.getProjectStatus = () =>
                Promise.resolve(
                    getMockedProjectStatus({
                        tasks: [getMockedProjectStatusTask({ ready_to_train: false })],
                    })
                );

            await renderTrainModel({
                models: [],
                projectService,
                FEATURE_FLAG_CREDIT_SYSTEM: false,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
            });

            fireEvent.click(screen.getByRole('button', { name: 'Train new model' }));

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByRole('heading', { name: 'Not enough annotations' })).toBeInTheDocument();
        });

        it('shows not enough annotations when training is not allowed and FEATURE_FLAG_CREDIT_SYSTEM is enabled', async () => {
            const projectService = createInMemoryProjectService();
            projectService.getProjectStatus = () =>
                Promise.resolve(
                    getMockedProjectStatus({
                        tasks: [getMockedProjectStatusTask({ ready_to_train: false })],
                    })
                );

            jest.mocked(useTotalCreditPrice).mockReturnValue({
                getCreditPrice: () => ({ totalCreditsToConsume: 1, totalMedias: 1 }),
                isLoading: false,
            });

            await renderTrainModel({
                models: [],
                projectService,
                FEATURE_FLAG_CREDIT_SYSTEM: true,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
            });

            fireEvent.click(screen.getByRole('button', { name: 'Train new model' }));

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByRole('heading', { name: 'Not enough annotations' })).toBeInTheDocument();
            fireEvent.click(screen.getByRole('button', { name: 'Annotate interactively' }));
            expect(mockedUseNavigate).toHaveBeenCalledWith(expect.stringContaining('/annotator'));
        });

        it('open/close modal when training is allowed and FEATURE_FLAG_CREDIT_SYSTEM is enabled and there are enough credits', async () => {
            const projectService = createInMemoryProjectService();
            projectService.getProjectStatus = () =>
                Promise.resolve(
                    getMockedProjectStatus({
                        tasks: [getMockedProjectStatusTask({ ready_to_train: true })],
                    })
                );

            const creditsService = createInMemoryCreditsService();
            creditsService.getOrganizationBalance = () =>
                Promise.resolve({
                    available: 10,
                    blocked: 0,
                    incoming: 0,
                });

            jest.mocked(useTotalCreditPrice).mockReturnValue({
                getCreditPrice: () => ({ totalCreditsToConsume: 1, totalMedias: 1 }),
                isLoading: false,
            });

            await renderTrainModel({
                models: [],
                projectService,
                creditsService,
                FEATURE_FLAG_CREDIT_SYSTEM: true,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
            });

            fireEvent.click(screen.getByRole('button', { name: 'Train new model' }));

            expect(screen.getByRole('dialog')).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

            await waitFor(() => {
                expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            });
        });

        it('shows not enough credits dialog when training is allowed and FEATURE_FLAG_CREDIT_SYSTEM is enabled and there are not enough credits', async () => {
            const projectService = createInMemoryProjectService();
            projectService.getProjectStatus = () =>
                Promise.resolve(
                    getMockedProjectStatus({
                        tasks: [getMockedProjectStatusTask({ ready_to_train: true })],
                    })
                );

            const creditsService = createInMemoryCreditsService();
            creditsService.getOrganizationBalance = () =>
                Promise.resolve({
                    available: 10,
                    blocked: 0,
                    incoming: 0,
                });

            jest.mocked(useTotalCreditPrice).mockReturnValue({
                getCreditPrice: () => ({ totalCreditsToConsume: 11, totalMedias: 1 }),
                isLoading: false,
            });

            await renderTrainModel({
                models: [],
                projectService,
                creditsService,
                FEATURE_FLAG_CREDIT_SYSTEM: true,
                FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
            });

            fireEvent.click(screen.getByRole('button', { name: 'Train new model' }));

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByRole('heading', { name: 'Not enough credits' })).toBeInTheDocument();
        });
    });
});
