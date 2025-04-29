// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useOverlayTriggerState } from '@react-stately/overlays';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import { CreditsService } from '../../../../../core/credits/services/credits-service.interface';
import { createInMemoryCreditsService } from '../../../../../core/credits/services/in-memory-credits-service';
import { FeatureFlags } from '../../../../../core/feature-flags/services/feature-flag-service.interface';
import { LABEL_BEHAVIOUR } from '../../../../../core/labels/label.interface';
import { createInMemoryMediaService } from '../../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { MediaService } from '../../../../../core/media/services/media-service.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
import { useDataset } from '../../../../../providers/dataset-provider/dataset-provider.component';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedPerformance, getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { RequiredProviders } from '../../../../../test-utils/required-providers-render';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { MORE_MEDIAS_MESSAGE, START_TRAINING_MESSAGE, useShowStartTraining } from './use-show-start-training.hook';

jest.mock('../../../providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../providers/project-provider/project-provider.component'),
    useProject: jest.fn(),
}));

jest.mock('../../../../../providers/dataset-provider/dataset-provider.component', () => ({
    ...jest.requireActual('../../../../../providers/dataset-provider/dataset-provider.component'),
    useDataset: jest.fn(),
}));

jest.mock('../../../../annotator/hooks/use-dataset-identifier.hook', () => ({
    ...jest.requireActual('../../../../annotator/hooks/use-dataset-identifier.hook'),
    useDatasetIdentifier: jest.fn(),
}));

const mockInvalidateQueries = jest.fn();
jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useQueryClient: () => ({
        invalidateQueries: mockInvalidateQueries,
    }),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
    }),
}));

const anomalyLabels = [
    getMockedLabel({
        id: 'normal',
        name: 'Normal',
        behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.EXCLUSIVE,
    }),
    getMockedLabel({
        id: 'anomalous',
        name: 'Anomalous',
        behaviour: LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.ANOMALOUS,
    }),
];

const anomalyProject = getMockedProject({
    tasks: [{ id: 'anomaly', domain: DOMAIN.ANOMALY_CLASSIFICATION, title: 'Anomaly', labels: anomalyLabels }],
});
const TRAINING_DIALOG_TEXT = 'training dialog is open';
const renderApp = ({
    featureFlags,
    mediaService = createInMemoryMediaService(),
    creditsService = createInMemoryCreditsService(),
}: {
    featureFlags?: Partial<FeatureFlags>;
    mediaService?: MediaService;
    creditsService?: CreditsService;
}) => {
    const App = () => {
        const state = useOverlayTriggerState({});
        useShowStartTraining(state);
        return <>{state.isOpen && <p>{TRAINING_DIALOG_TEXT}</p>}</>;
    };
    render(
        <RequiredProviders featureFlags={featureFlags} mediaService={mediaService} creditsService={creditsService}>
            <App />
        </RequiredProviders>
    );
};

describe('useShowStartTraining', () => {
    beforeEach(() => {
        // @ts-expect-error We only wish to mock the project
        jest.mocked(useProject).mockImplementation(() => ({
            project: anomalyProject,
            isSingleDomainProject: () => true,
        }));

        // @ts-expect-error We only wish to mock the selected dataset
        jest.mocked(useDataset).mockImplementation(() => ({
            selectedDataset: anomalyProject.datasets[0],
        }));

        jest.mocked(useDatasetIdentifier).mockImplementation(() => ({
            organizationId: 'organization-id',
            workspaceId: 'workspace-id',
            projectId: anomalyProject.id,
            datasetId: anomalyProject.datasets[0].id,
        }));
    });

    it('if the project has trained models, the start-training notification should not show', async () => {
        // @ts-expect-error We only wish to mock the project
        jest.mocked(useProject).mockImplementation(() => ({
            project: {
                ...anomalyProject,
                performance: {
                    type: 'default_performance',
                    score: 1.0,
                },
            },
            isSingleDomainProject: () => true,
        }));

        renderApp({});

        await waitFor(() => {
            expect(screen.queryByText(START_TRAINING_MESSAGE)).not.toBeInTheDocument();
            expect(screen.queryByText(MORE_MEDIAS_MESSAGE)).not.toBeInTheDocument();
        });
    });

    describe('the project does not have trained models', () => {
        it('the user did not upload the necessary media to start training, a warning should show', async () => {
            // @ts-expect-error We only wish to mock the project
            jest.mocked(useProject).mockImplementation(() => ({
                project: {
                    ...anomalyProject,
                    performance: getMockedPerformance({ ...anomalyProject, performance: undefined }, null),
                },
                isSingleDomainProject: () => true,
            }));

            const mediaService = createInMemoryMediaService();
            mediaService.getAdvancedFilterMedia = async () => {
                return {
                    nextPage: undefined,
                    media: [],
                    totalImages: 0,
                    totalMatchedImages: 0,
                    totalMatchedVideoFrames: 0,
                    totalMatchedVideos: 0,
                    totalVideos: 0,
                };
            };

            renderApp({ mediaService });

            await waitFor(() => {
                expect(screen.queryByText(MORE_MEDIAS_MESSAGE)).toBeVisible();
                expect(screen.queryByText(START_TRAINING_MESSAGE)).not.toBeInTheDocument();
            });
        });

        it('the start-training notification should show', async () => {
            // @ts-expect-error We only wish to mock the project
            jest.mocked(useProject).mockImplementation(() => ({
                project: {
                    ...anomalyProject,
                    performance: getMockedPerformance({ ...anomalyProject, performance: undefined }, null),
                },
                isSingleDomainProject: () => true,
            }));

            // Using the default media service that returns 10 images and 10 frames
            renderApp({});

            // Make sure we don't show a notification while still loading
            expect(screen.queryByText(START_TRAINING_MESSAGE)).not.toBeInTheDocument();

            await waitFor(() => {
                expect(screen.queryByText(START_TRAINING_MESSAGE)).toBeVisible();
                expect(screen.queryByText(MORE_MEDIAS_MESSAGE)).not.toBeInTheDocument();
            });
        });

        it('opens training dialog', async () => {
            // @ts-expect-error We only wish to mock the project
            jest.mocked(useProject).mockImplementation(() => ({
                project: {
                    ...anomalyProject,
                    performance: getMockedPerformance({ ...anomalyProject, performance: undefined }, null),
                },
                isSingleDomainProject: () => true,
            }));

            renderApp({});

            await waitFor(() => {
                expect(screen.queryByText(START_TRAINING_MESSAGE)).toBeVisible();
                expect(screen.queryByText(MORE_MEDIAS_MESSAGE)).not.toBeInTheDocument();
            });

            fireEvent.click(screen.getByRole('button', { name: /train/i }));

            expect(screen.queryByText(TRAINING_DIALOG_TEXT)).toBeVisible();
        });

        it('CREDIT_SYSTEM enabled, the start-training notification should show', async () => {
            // @ts-expect-error We only wish to mock the project
            jest.mocked(useProject).mockImplementation(() => ({
                project: {
                    ...anomalyProject,
                    performance: getMockedPerformance({ ...anomalyProject, performance: undefined }, null),
                },
                isSingleDomainProject: () => true,
            }));

            // Using the default media service that returns 10 iamges and 10 frames
            renderApp({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true } });

            await waitFor(() => {
                expect(screen.queryByText(START_TRAINING_MESSAGE)).toBeVisible();
                expect(screen.queryByText(MORE_MEDIAS_MESSAGE)).not.toBeInTheDocument();
            });
        });

        it('CREDIT_SYSTEM enabled, should not showing the notification if not enough credits', async () => {
            const creditsService = createInMemoryCreditsService();
            creditsService.getOrganizationBalance = jest.fn().mockResolvedValue({ available: 0, incoming: 0 });
            // @ts-expect-error We only wish to mock the project
            jest.mocked(useProject).mockImplementation(() => ({
                project: {
                    ...anomalyProject,
                    performance: getMockedPerformance({ ...anomalyProject, performance: undefined }, null),
                },
                isSingleDomainProject: () => true,
            }));

            renderApp({ featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: true }, creditsService });

            await waitFor(() => {
                expect(screen.queryByText(START_TRAINING_MESSAGE)).not.toBeInTheDocument();
            });
        });

        it('invalidates the project status query when the start-training notification is shown', async () => {
            // @ts-expect-error We only wish to mock the project
            jest.mocked(useProject).mockImplementation(() => ({
                project: {
                    ...anomalyProject,
                    performance: getMockedPerformance({ ...anomalyProject, performance: undefined }, null),
                },
                isSingleDomainProject: () => true,
            }));

            renderApp({});

            await waitFor(() => {
                expect(screen.queryByText(START_TRAINING_MESSAGE)).toBeVisible();
            });

            expect(mockInvalidateQueries).toHaveBeenCalledWith({
                queryKey: QUERY_KEYS.PROJECT_STATUS_KEY({
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                }),
            });
        });
    });
});
