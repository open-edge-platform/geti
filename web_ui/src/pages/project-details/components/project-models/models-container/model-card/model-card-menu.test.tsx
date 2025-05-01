// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { delay } from '@shared/utils';
import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { CreditsService } from '../../../../../../core/credits/services/credits-service.interface';
import { createInMemoryCreditsService } from '../../../../../../core/credits/services/in-memory-credits-service';
import { FeatureFlags } from '../../../../../../core/feature-flags/services/feature-flag-service.interface';
import { createInMemoryModelsService } from '../../../../../../core/models/services/in-memory-models-service';
import { ModelsService } from '../../../../../../core/models/services/models.interface';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedModelVersion } from '../../../../../../test-utils/mocked-items-factory/mocked-model';
import { providersRender } from '../../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../../providers/project-provider/project-provider.component';
import { ModelCardMenu } from './model-card-menu.component';
import { ModelVersion } from './model-card.interface';
import { ACTIVATED_MODEL_MESSAGE } from './utils';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
    }),
}));

describe('ModelCardMenu', () => {
    afterAll(() => {
        jest.clearAllTimers();
    });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const modelActive = getMockedModelVersion({ isActiveModel: true });
    const modelInactive = getMockedModelVersion({ isActiveModel: false });

    const activateModel = jest.fn(() => Promise.resolve());
    const trainModel = jest.fn(() => Promise.resolve());

    const defaultModelsService = createInMemoryModelsService();
    defaultModelsService.activateModel = activateModel;
    defaultModelsService.trainModel = trainModel;

    const defaultCreditsService = createInMemoryCreditsService();

    const render = async ({
        model = modelActive,
        isLatestModel = true,
        modelsService = defaultModelsService,
        creditsService = defaultCreditsService,
        featureFlags = { FEATURE_FLAG_CREDIT_SYSTEM: false },
    }: {
        model?: ModelVersion;
        isLatestModel?: boolean;
        modelsService?: ModelsService;
        creditsService?: CreditsService;
        featureFlags?: Partial<FeatureFlags>;
    }) => {
        providersRender(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <ModelCardMenu
                    model={model}
                    taskId={'1'}
                    projectIdentifier={{
                        groupId: '',
                        modelId: '',
                        projectId: '',
                        workspaceId: '',
                        organizationId: '',
                    }}
                    isLatestModel={isLatestModel}
                    isMenuOptionsDisabled={false}
                    modelTemplateId={'template-id'}
                />
            </ProjectProvider>,
            {
                services: { modelsService, creditsService },
                featureFlags,
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it("has 'Run test' option in the menu", async () => {
        await render({});

        fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

        expect(screen.getByRole('menuitem', { name: /run test/i })).toBeVisible();
    });

    it("has 'Set as active model' option in the menu if it's the latest model and model is inactive", async () => {
        await render({ model: modelInactive });

        fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

        expect(screen.getByRole('menuitem', { name: /set as active model/i })).toBeInTheDocument();
    });

    it("not has 'Set as active model' option in the menu if it's not the latest model", async () => {
        await render({ model: modelInactive, isLatestModel: false });

        fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

        expect(screen.queryByRole('menuitem', { name: /set as active model/i })).not.toBeInTheDocument();
    });

    describe('Retrain model', () => {
        it('has "Retrain" option only for the latest active model', async () => {
            await render({ model: modelActive, isLatestModel: true });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

            expect(screen.getByRole('menuitem', { name: /retrain/i })).toBeInTheDocument();
        });

        it('has no "Retrain" option when the model is not active', async () => {
            await render({ model: modelInactive, isLatestModel: true });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

            expect(screen.queryByRole('menuitem', { name: /retrain/i })).not.toBeInTheDocument();
        });

        it('has no "Retrain" option when model is not latest', async () => {
            await render({ model: modelActive, isLatestModel: false });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

            expect(screen.queryByRole('menuitem', { name: /retrain/i })).not.toBeInTheDocument();
        });

        it('has no "Retrain" option when model is not latest and model is not active', async () => {
            await render({ model: modelInactive, isLatestModel: false });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

            expect(screen.queryByRole('menuitem', { name: /retrain/i })).not.toBeInTheDocument();
        });
    });

    describe('Archive model', () => {
        describe('"archive" option is hidden', () => {
            it('active model', async () => {
                await render({
                    model: getMockedModelVersion({ isActiveModel: true }),
                    isLatestModel: false,
                });

                fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

                expect(screen.queryByRole('menuitem', { name: /archive/i })).not.toBeInTheDocument();
            });

            it('it is the latest model', async () => {
                await render({
                    model: getMockedModelVersion({ isActiveModel: false }),
                    isLatestModel: true,
                });

                fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

                expect(screen.queryByRole('menuitem', { name: /archive/i })).not.toBeInTheDocument();
            });
        });

        it('model menu is hidden for deleted items', async () => {
            await render({
                model: getMockedModelVersion({
                    isActiveModel: false,
                    purgeInfo: { isPurged: true, userId: 'userId', purgeTime: 'purgeTime' },
                }),
                isLatestModel: false,
            });

            expect(screen.queryByRole('button', { name: /model action menu/i })).not.toBeInTheDocument();
        });

        it('displays archive modal', async () => {
            const groupName = 'test-name';

            await render({
                model: getMockedModelVersion({ isActiveModel: false, groupName }),
                isLatestModel: false,
            });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));
            fireEvent.click(screen.getByRole('menuitem', { name: /delete/i }));

            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(screen.getByText(`${groupName} model version 1`)).toBeInTheDocument();
        });
    });

    describe("Labels' schema", () => {
        const modelInactiveAndLabelsOutdated = getMockedModelVersion({
            isActiveModel: false,
            isLabelSchemaUpToDate: false,
        });

        it("does not display model activation dialog when labels' schema is up to date", async () => {
            await render({
                model: getMockedModelVersion({ isActiveModel: false, isLabelSchemaUpToDate: true }),
            });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));
            fireEvent.click(screen.getByRole('menuitem', { name: /set as active model/i }));

            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        it("display model activation dialog when labels' schema is outdated and model is inactive", async () => {
            await render({
                model: getMockedModelVersion({ isActiveModel: false, isLabelSchemaUpToDate: false }),
            });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));
            fireEvent.click(screen.getByRole('menuitem', { name: /set as active model/i }));

            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });

        it("invoke 'activateModel' callback, show loading indicator and show notification info when user presses 'Set as active'", async () => {
            const { templateName, groupName, version } = modelInactiveAndLabelsOutdated;
            const modelName = `${templateName} (${groupName})`;
            const mockedModelService = createInMemoryModelsService();
            mockedModelService.activateModel = jest.fn(async () => {
                // Simulate loading
                await delay(1000);
                return Promise.resolve();
            });
            await render({ model: modelInactiveAndLabelsOutdated, modelsService: mockedModelService });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));
            fireEvent.click(screen.getByRole('menuitem', { name: /set as active model/i }));

            jest.useFakeTimers();

            fireEvent.click(screen.getByTestId('set-as-active-id'));

            expect(await screen.findByRole('progressbar')).toBeVisible();

            jest.runAllTimers();
            jest.useRealTimers();

            await waitFor(() => {
                expect(mockedModelService.activateModel).toHaveBeenCalled();
                expect(screen.getByText(ACTIVATED_MODEL_MESSAGE(modelName, version))).toBeInTheDocument();
            });
        });

        it("invoke 'activateModel' and 'trainModel' callbacks when user press 'Set as active & retrain'", async () => {
            const { templateName, groupName, version } = modelInactiveAndLabelsOutdated;
            const modelName = `${templateName} (${groupName})`;

            await render({ model: modelInactiveAndLabelsOutdated });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));
            fireEvent.click(screen.getByRole('menuitem', { name: /set as active model/i }));

            fireEvent.click(screen.getByTestId('set-as-active-retrain-id'));

            await waitFor(() => {
                expect(activateModel).toHaveBeenCalled();
                expect(screen.getByText(ACTIVATED_MODEL_MESSAGE(modelName, version))).toBeInTheDocument();
                expect(trainModel).toHaveBeenCalled();
            });
        });

        it("if invoking 'activateModel' fails it should not invoke 'trainModel' callback when user press 'Set as active & retrain'", async () => {
            const modelsService = createInMemoryModelsService();
            modelsService.activateModel = jest.fn(() => Promise.reject({ message: 'Failed in activating model' }));
            modelsService.trainModel = jest.fn();

            const { templateName, groupName, version } = modelInactiveAndLabelsOutdated;
            const modelName = `${templateName} (${groupName})`;

            await render({ model: modelInactiveAndLabelsOutdated, isLatestModel: true, modelsService });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));
            fireEvent.click(screen.getByRole('menuitem', { name: /set as active model/i }));

            fireEvent.click(screen.getByTestId('set-as-active-retrain-id'));

            await waitFor(() => {
                expect(modelsService.activateModel).toHaveBeenCalled();
                expect(screen.queryByText(ACTIVATED_MODEL_MESSAGE(modelName, version))).not.toBeInTheDocument();
                expect(modelsService.trainModel).not.toHaveBeenCalled();
            });
        });

        it('Credit system feature flag is enabled and balance is loading -> Retrain is disabled', async () => {
            const creditsService = createInMemoryCreditsService();
            creditsService.getOrganizationBalance = jest.fn(async () => {
                // Simulate loading
                await delay(1000);
                return Promise.resolve({ available: 0, incoming: 0, blocked: 0 });
            });
            await render({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true }, creditsService });

            jest.useFakeTimers();

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

            await waitFor(() => {
                expect(screen.getByRole('menuitem', { name: /retrain/i })).toHaveAttribute('aria-disabled', 'true');
            });

            jest.runAllTimers();
            jest.useRealTimers();
        });

        it('Credit system feature flag is enabled and balance is not enough -> Not enough credits dialog is shown', async () => {
            const creditsService = createInMemoryCreditsService();
            creditsService.getOrganizationBalance = jest.fn(() => {
                return new Promise((resolve) => resolve({ available: 0, incoming: 0, blocked: 0 }));
            });

            await render({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true }, creditsService });
            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

            await waitFor(() => {
                expect(screen.getByRole('menuitem', { name: /retrain/i })).not.toHaveAttribute('aria-disabled', 'true');
            });

            fireEvent.click(screen.getByRole('menuitem', { name: /retrain/i }));

            expect(screen.getByText('Not enough credits')).toBeInTheDocument();
        });

        it('Credit system feature flag is enabled and balance is enough -> Retrain endpoint should be triggered', async () => {
            const modelsService = createInMemoryModelsService();
            modelsService.trainModel = jest.fn();

            await render({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true }, modelsService });

            fireEvent.click(screen.getByRole('button', { name: /model action menu/i }));

            await waitFor(() => {
                expect(screen.getByRole('menuitem', { name: /retrain/i })).not.toHaveAttribute('aria-disabled', 'true');
            });

            fireEvent.click(screen.getByRole('menuitem', { name: /retrain/i }));

            await waitFor(() => {
                expect(modelsService.trainModel).toHaveBeenCalled();
            });
        });
    });
});
