// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OverlayTriggerState } from '@react-stately/overlays';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import { FeatureFlags } from '../../../../core/feature-flags/services/feature-flag-service.interface';
import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { TOO_LOW_FREE_DISK_SPACE_IN_BYTES } from '../../../../core/status/hooks/utils';
import { createInMemoryStatusService } from '../../../../core/status/services/in-memory-status-service';
import {
    ExportImportDatasetDialogProvider,
    useExportImportDatasetDialogStates,
} from '../../../../features/dataset-export/components/export-import-dataset-dialog-provider.component';
import { DatasetImportToExistingProjectProvider } from '../../../../features/dataset-import/providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { DatasetProvider } from '../../../../providers/dataset-provider/dataset-provider.component';
import { MediaUploadProvider } from '../../../../providers/media-upload-provider/media-upload-provider.component';
import { applicationRender as render } from '../../../../test-utils/application-provider-render';
import { getMockedDataset } from '../../../../test-utils/mocked-items-factory/mocked-datasets';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { getById } from '../../../../test-utils/utils';
import { MediaProvider } from '../../../media/providers/media-provider.component';
import { ProjectProvider } from '../../providers/project-provider/project-provider.component';
import { ProjectDatasetTabActions, ProjectDatasetTabActionsProps } from './project-dataset-tab-actions.component';
import { DatasetTabActions } from './utils';

jest.mock('../../../../features/dataset-export/components/export-import-dataset-dialog-provider.component', () => ({
    ...jest.requireActual(
        '../../../../features/dataset-export/components/export-import-dataset-dialog-provider.component'
    ),
    useExportImportDatasetDialogStates: jest.fn(),
}));

describe('ProjectDatasetTabActions', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.clearAllMocks();
        jest.clearAllTimers();
        jest.useRealTimers();
    });

    const mockDatasetImportDialogState = {
        isOpen: false,
        setOpen: jest.fn(),
        open: jest.fn(),
        close: jest.fn(),
        toggle: jest.fn(),
    };

    const mockDatasetExportDialogState = {
        isOpen: false,
        setOpen: jest.fn(),
        open: jest.fn(),
        close: jest.fn(),
        toggle: jest.fn(),
    };

    const getMenuItem = (name: string) => screen.getByRole('menuitem', { name });

    const renderApp = async ({
        dataset = getMockedDataset(),
        hasMedia = true,
        isTaskChainProject = false,
        freeSpace = TOO_LOW_FREE_DISK_SPACE_IN_BYTES + 1,
        exportDialogState = mockDatasetExportDialogState,
        domain = DOMAIN.DETECTION,
        featureFlags,
    }: Partial<
        ProjectDatasetTabActionsProps & {
            freeSpace: number;
            exportDialogState: OverlayTriggerState;
            hasMedia: boolean;
            isTaskChainProject: boolean;
            domain?: DOMAIN;
            featureFlags?: Partial<FeatureFlags>;
        }
    >) => {
        jest.mocked(useExportImportDatasetDialogStates).mockReturnValue({
            datasetImportDialogState: mockDatasetImportDialogState,
            exportDialogState,
        });

        const statusService = createInMemoryStatusService();
        statusService.getStatus = async () => ({ freeSpace, runningJobs: 10, totalSpace: 0 });

        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => {
            return getMockedProject({
                tasks: isTaskChainProject
                    ? [getMockedTask({ id: '1', domain }), getMockedTask({ id: '2', domain: DOMAIN.SEGMENTATION })]
                    : [getMockedTask({ id: '1', domain })],
                datasets: [dataset],
            });
        };

        const mediaService = hasMedia ? createInMemoryMediaService() : createInMemoryMediaService([]);

        return await render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
                <MediaUploadProvider>
                    <DatasetProvider>
                        <MediaProvider>
                            <DatasetImportToExistingProjectProvider>
                                <ExportImportDatasetDialogProvider>
                                    <ProjectDatasetTabActions dataset={dataset} />
                                </ExportImportDatasetDialogProvider>
                            </DatasetImportToExistingProjectProvider>
                        </MediaProvider>
                    </DatasetProvider>
                </MediaUploadProvider>
            </ProjectProvider>,
            { services: { mediaService, projectService, statusService }, featureFlags }
        );
    };

    it('should render dataset actions button if tab is selected', async () => {
        const { container } = await renderApp({});

        expect(getById(container, 'dataset-actions')).toBeInTheDocument();
    });

    it('should open/close export dataset dialog', async () => {
        await renderApp({});

        expect(screen.getByLabelText('open dataset menu')).toBeTruthy();

        // Trigger menu popover
        fireEvent.click(screen.getByLabelText('open dataset menu'));

        // Press "Export dataset" option to trigger dialog
        fireEvent.click(await screen.findByText(DatasetTabActions.ExportDataset));

        expect(mockDatasetExportDialogState.open).toHaveBeenCalledTimes(1);
    });

    it('disables import/export options when the FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE is off', async () => {
        await renderApp({
            isTaskChainProject: false,
            domain: DOMAIN.KEYPOINT_DETECTION,
            featureFlags: { FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE: false },
        });

        expect(screen.getByLabelText('open dataset menu')).toBeTruthy();

        // Trigger menu popover
        fireEvent.click(screen.getByLabelText('open dataset menu'));

        expect(screen.getByRole('menuitem', { name: DatasetTabActions.ExportDataset })).toHaveAttribute(
            'aria-disabled',
            'true'
        );
        expect(screen.getByRole('menuitem', { name: DatasetTabActions.ImportDataset })).toHaveAttribute(
            'aria-disabled',
            'true'
        );
    });

    it('should show export dataset dialog', async () => {
        await renderApp({
            exportDialogState: {
                isOpen: true,
                setOpen: jest.fn(),
                open: jest.fn(),
                close: jest.fn(),
                toggle: jest.fn(),
            },
        });

        expect(screen.getByText('Select dataset export format')).toBeInTheDocument();
    });

    describe('Menu actions', () => {
        it('should show "export dataset" if dataset has media items', async () => {
            await renderApp({ dataset: getMockedDataset({ useForTraining: true }) });

            // Trigger menu popover
            fireEvent.click(screen.getByLabelText('open dataset menu'));

            expect(await screen.findByText(DatasetTabActions.ExportDataset)).toBeInTheDocument();
            expect(screen.getByText(DatasetTabActions.ImportDataset)).toBeInTheDocument();
            expect(screen.queryByText(DatasetTabActions.UpdateDataset)).not.toBeInTheDocument();
            expect(screen.queryByText(DatasetTabActions.DeleteDataset)).not.toBeInTheDocument();
        });

        it('should show "Import dataset", "Delete dataset", "Edit dataset name" if testing set is selected and there are no media items', async () => {
            await renderApp({
                dataset: getMockedDataset({ useForTraining: false }),
                hasMedia: false,
            });

            // Trigger menu popover
            fireEvent.click(screen.getByLabelText('open dataset menu'));

            const importDataset = getMenuItem(DatasetTabActions.ImportDataset);
            expect(importDataset).toBeInTheDocument();

            // Wait for storage status to have finished loading
            await waitFor(() => {
                expect(importDataset).not.toHaveAttribute('aria-disabled');
            });

            const deleteDataset = getMenuItem(DatasetTabActions.DeleteDataset);
            expect(deleteDataset).toBeInTheDocument();
            expect(deleteDataset).not.toHaveAttribute('aria-disabled');

            const updateDataset = getMenuItem(DatasetTabActions.UpdateDataset);
            expect(updateDataset).toBeInTheDocument();
            expect(updateDataset).not.toHaveAttribute('aria-disabled');

            expect(screen.queryByText(DatasetTabActions.ExportDataset)).not.toBeInTheDocument();
        });

        it('should not show "Import dataset" option for task chain project', async () => {
            await renderApp({
                hasMedia: true,
                isTaskChainProject: true,
                dataset: getMockedDataset({ useForTraining: false }),
            });

            // Trigger menu popover
            fireEvent.click(screen.getByLabelText('open dataset menu'));

            expect(screen.queryByText(DatasetTabActions.ImportDataset)).not.toBeInTheDocument();
            expect(screen.getByText(DatasetTabActions.DeleteDataset)).toBeInTheDocument();
            expect(await screen.findByText(DatasetTabActions.ExportDataset)).toBeInTheDocument();
            expect(screen.getByText(DatasetTabActions.UpdateDataset)).toBeInTheDocument();
        });

        it('low storage space disables import options', async () => {
            await renderApp({
                dataset: getMockedDataset({ useForTraining: false }),
                freeSpace: 0,
            });

            // Trigger menu popover
            fireEvent.click(screen.getByLabelText('open dataset menu'));

            const importDataset = getMenuItem(DatasetTabActions.ImportDataset);

            expect(importDataset).toBeInTheDocument();
            expect(importDataset).toHaveAttribute('aria-disabled', 'true');
        });

        it('open import modal', async () => {
            await renderApp({
                dataset: getMockedDataset({ useForTraining: false }),
            });

            // Trigger menu popover
            fireEvent.click(screen.getByLabelText('open dataset menu'));

            const importDataset = getMenuItem(DatasetTabActions.ImportDataset);

            await waitFor(() => {
                expect(importDataset).not.toHaveAttribute('aria-disabled');
            });

            fireEvent.click(importDataset);

            expect(mockDatasetImportDialogState.open).toHaveBeenCalledTimes(1);
        });

        it('open delete modal', async () => {
            await renderApp({
                dataset: getMockedDataset({ useForTraining: false }),
            });

            // Trigger menu popover
            fireEvent.click(screen.getByLabelText('open dataset menu'));

            const importDataset = getMenuItem(DatasetTabActions.DeleteDataset);

            fireEvent.click(importDataset);

            expect(screen.getByText('Are you sure you want to delete "Training dataset"?')).toBeVisible();
        });
    });
});
