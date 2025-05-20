// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ApplicationServicesContextProps } from '@geti/core/src/services/application-services-provider.component';
import { useNavigateToAnnotatorRoute } from '@geti/core/src/services/use-navigate-to-annotator-route.hook';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import { LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Dataset } from '../../../../core/projects/dataset.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { ExportImportDatasetDialogProvider } from '../../../../features/dataset-export/components/export-import-dataset-dialog-provider.component';
import { DatasetImportToExistingProjectProvider } from '../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { DatasetProvider } from '../../../../providers/dataset-provider/dataset-provider.component';
import { MediaUploadProvider } from '../../../../providers/media-upload-provider/media-upload-provider.component';
import { getMockedDataset } from '../../../../test-utils/mocked-items-factory/mocked-datasets';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { MediaProvider } from '../../../media/providers/media-provider.component';
import { DatasetTabPanel } from './dataset-tab-panel.component';
import { NO_MEDIA_MESSAGE } from './utils';

jest.mock('@geti/core/src/services/use-navigate-to-annotator-route.hook', () => ({
    ...jest.requireActual('@geti/core/src/services/use-navigate-to-annotator-route.hook'),
    useNavigateToAnnotatorRoute: jest.fn(),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
        organizationId: 'organization-id',
    }),
}));

jest.mock('./hooks/open-notification-toast.hook', () => ({
    useOpenNotificationToast: jest.fn(),
}));

describe('DatasetTabPanel', () => {
    const renderDatasetTabPanel = async ({
        selectedDataset,
        services,
    }: {
        selectedDataset?: Dataset;
        services?: Partial<ApplicationServicesContextProps>;
    }) => {
        const dataset: Dataset = selectedDataset ?? getMockedDataset();

        await render(
            <MediaUploadProvider>
                <DatasetProvider>
                    <MediaUploadProvider>
                        <MediaProvider>
                            <DatasetImportToExistingProjectProvider>
                                <ExportImportDatasetDialogProvider>
                                    <DatasetTabPanel dataset={dataset} />
                                </ExportImportDatasetDialogProvider>
                            </DatasetImportToExistingProjectProvider>
                        </MediaProvider>
                    </MediaUploadProvider>
                </DatasetProvider>
            </MediaUploadProvider>,
            { services }
        );
    };

    it('should render a menu with export and import dataset if it is a single anomaly project', async () => {
        const projectService = createInMemoryProjectService();

        projectService.getProject = jest.fn(async () =>
            getMockedProject({
                tasks: [
                    getMockedTask({
                        id: 'task-id',
                        domain: DOMAIN.ANOMALY_CLASSIFICATION,
                        labels: [
                            getMockedLabel({ name: 'Anomalous', behaviour: LABEL_BEHAVIOUR.ANOMALOUS }),
                            getMockedLabel({ name: 'Normal', behaviour: LABEL_BEHAVIOUR.EXCLUSIVE }),
                        ],
                    }),
                ],
            })
        );

        await renderDatasetTabPanel({ services: { projectService } });

        expect(await screen.findByRole('button', { name: /export or import dataset/i })).toBeInTheDocument();
        expect(screen.getByText('Explore')).toBeInTheDocument();
    });

    it('renders a menu with export and import dataset for non anomaly projects', async () => {
        const projectService = createInMemoryProjectService();

        projectService.getProject = jest.fn(async () =>
            getMockedProject({
                tasks: [getMockedTask({ id: 'task-id', domain: DOMAIN.CLASSIFICATION })],
            })
        );

        await renderDatasetTabPanel({ services: { projectService } });

        expect(await screen.findByRole('button', { name: /export or import dataset/i })).toBeInTheDocument();
        expect(screen.getByText('Annotate interactively')).toBeInTheDocument();
    });

    it('should render a button with "Explore" string if it is a single anomaly project', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = jest.fn(async () =>
            getMockedProject({
                tasks: [
                    getMockedTask({
                        id: 'task-id',
                        domain: DOMAIN.ANOMALY_CLASSIFICATION,
                        labels: [
                            getMockedLabel({ name: 'Anomalous', behaviour: LABEL_BEHAVIOUR.ANOMALOUS }),
                            getMockedLabel({ name: 'Normal', behaviour: LABEL_BEHAVIOUR.EXCLUSIVE }),
                        ],
                    }),
                ],
                domains: [DOMAIN.ANOMALY_CLASSIFICATION],
            })
        );

        await renderDatasetTabPanel({ services: { projectService } });

        expect(screen.getByText('Explore')).toBeInTheDocument();
    });

    it('should render a button with "Annotate interactively" if it is NOT a single anomaly project', async () => {
        await renderDatasetTabPanel({});

        await waitFor(() => {
            expect(screen.getByRole('button', { name: 'Annotate interactively' })).toBeEnabled();
        });
    });

    it('should render a button with "Annotate Testing set" if the selected dataset is not used for training', async () => {
        const testingSet = getMockedDataset({ useForTraining: false, name: 'Testing set' });

        await renderDatasetTabPanel({
            selectedDataset: testingSet,
        });

        expect(screen.getByRole('button', { name: `Annotate ${testingSet.name}` })).toBeInTheDocument();
    });

    it('should trigger navigate to the annotator correctly', async () => {
        const navigateToAnnotatorRoute = jest.fn();
        jest.mocked(useNavigateToAnnotatorRoute).mockImplementation(navigateToAnnotatorRoute);

        await renderDatasetTabPanel({});

        fireEvent.click(screen.getByRole('button', { name: 'Annotate interactively' }));

        expect(navigateToAnnotatorRoute).toHaveBeenCalledTimes(1);
    });

    it('Annotate button should be DISABLED when there are no media items', async () => {
        await renderDatasetTabPanel({ services: { mediaService: createInMemoryMediaService([]) } });

        await checkTooltip(screen.getByLabelText('disabled tooltip trigger'), NO_MEDIA_MESSAGE);
        expect(screen.getByRole('button', { name: 'Annotate interactively' })).toBeDisabled();
    });
});
