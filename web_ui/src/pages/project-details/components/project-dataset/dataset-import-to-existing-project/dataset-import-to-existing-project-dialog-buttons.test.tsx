// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { DATASET_IMPORT_STATUSES } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportToExistingProjectItem } from '../../../../../core/datasets/dataset.interface';
import { providersRender } from '../../../../../test-utils/required-providers-render';
import { DatasetImportToExistingProjectDialogButtons } from './dataset-import-to-existing-project-dialog-buttons.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const mockDatasetImportItem: DatasetImportToExistingProjectItem = {
    id: '987-654-321',
    name: 'Test Dataset',
    size: '1Gb',
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    progress: 50,
    startAt: 0,
    startFromBytes: 0,
    uploadId: '192-837-465',
    bytesRemaining: '500Mb',
    timeRemaining: '10 minutes',
    warnings: [],
    labels: [],
    labelsMap: {},
    projectId: '',
    datasetId: '',
    datasetName: '',
};

const mockDeletionDialogTriggerState = {
    isOpen: false,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

const mockOnPrimaryAction = jest.fn();
const mockOnDialogDismiss = jest.fn();

const mockAbortDatasetImportAction = jest.fn();
const mockDeleteActiveDatasetImport = jest.fn();
const mockPatchActiveDatasetImport = jest.fn();

let mockIsReadyValue = false;

const mockAbortActiveUpload = jest.fn();
jest.mock('../../../../../providers/tus-upload-provider/tus-upload-provider.component', () => ({
    ...jest.requireActual('../../../../../providers/tus-upload-provider/tus-upload-provider.component'),
    useTusUpload: () => ({ abortActiveUpload: mockAbortActiveUpload }),
}));

jest.mock(
    '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component',
    () => ({
        ...jest.requireActual(
            '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
        ),
        useDatasetImportToExistingProject: jest.fn(() => ({
            abortDatasetImportAction: mockAbortDatasetImportAction,
            deleteActiveDatasetImport: mockDeleteActiveDatasetImport,
            patchActiveDatasetImport: mockPatchActiveDatasetImport,
            isReady: () => mockIsReadyValue,
        })),
    })
);

const renderMockedComponent = async (
    datasetImportItem: DatasetImportToExistingProjectItem | undefined,
    options?: Parameters<typeof providersRender>[1]
) => {
    return providersRender(
        <DatasetImportToExistingProjectDialogButtons
            isDisableWithDuplicates={false}
            deletionDialogTriggerState={mockDeletionDialogTriggerState}
            datasetImportItem={datasetImportItem}
            onPrimaryAction={mockOnPrimaryAction}
            onDialogDismiss={mockOnDialogDismiss}
        />,
        options
    );
};

describe(DatasetImportToExistingProjectDialogButtons, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('should properly render buttons depending on current step and datasetImportItem status', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
        ])('should show "Hide" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ ...mockDatasetImportItem, status });
            expect(screen.getByRole('button', { name: 'Hide' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
        ])('should show "Cancel" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ ...mockDatasetImportItem, status });
            expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
        ])('should hide "Cancel" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ ...mockDatasetImportItem, status });
            expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
        ])('should show "Delete" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ ...mockDatasetImportItem, status });
            expect(screen.getByRole('button', { name: 'Delete' })).toBeVisible();
        });

        it('should hide "Delete" button when there is no datasetImportItem', async () => {
            await renderMockedComponent(undefined);
            expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
        ])('should hide "Delete" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ ...mockDatasetImportItem, status });
            expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
        });

        it('should show "Import" button when the step is "labelMapping"', async () => {
            await renderMockedComponent({
                ...mockDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            });
            expect(screen.getByRole('button', { name: 'Import' })).toBeVisible();
        });

        it('should disable "Import" button when datasetImportItem is not ready', async () => {
            await renderMockedComponent({
                ...mockDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            });
            expect(screen.queryByRole('button', { name: 'Import' })).toBeDisabled();
        });
    });

    describe('should properly interact on each button click', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it('should call dialog dismiss on click to "Hide" button', async () => {
            await renderMockedComponent(mockDatasetImportItem);
            expect(screen.getByRole('button', { name: 'Hide' })).toBeVisible();
            fireEvent.click(screen.getByRole('button', { name: 'Hide' }));
            expect(mockOnDialogDismiss).toHaveBeenCalled();
        });

        it('should abort tus upload request and remove activeDatasetImportItem on click to "Cancel" button', async () => {
            mockAbortActiveUpload.mockResolvedValue(true);

            await renderMockedComponent({ ...mockDatasetImportItem, status: DATASET_IMPORT_STATUSES.UPLOADING });
            expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();
            fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

            await waitFor(() => {
                expect(mockAbortActiveUpload).toHaveBeenCalledWith('987-654-321');
                expect(mockDeleteActiveDatasetImport).toHaveBeenCalled();
            });
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
        ])(': cancel job and remove activeDatasetImportItem on click to "Cancel" button', async ({ status }) => {
            await renderMockedComponent(
                { ...mockDatasetImportItem, preparingJobId: '123', importingJobId: '321', status },
                undefined
            );
            expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();
            fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
            expect(mockAbortDatasetImportAction).not.toHaveBeenCalled();
            expect(mockDeleteActiveDatasetImport).toHaveBeenCalled();
        });

        it('should open deletion dialog on click to "Delete" button', async () => {
            await renderMockedComponent({
                ...mockDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            });
            expect(screen.getByRole('button', { name: 'Delete' })).toBeVisible();
            fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
            expect(mockDeletionDialogTriggerState.open).toHaveBeenCalled();
        });

        it('should call onPrimaryAction and onDialogDismiss on click to "Import" button', async () => {
            mockIsReadyValue = true;

            await renderMockedComponent({ ...mockDatasetImportItem, status: DATASET_IMPORT_STATUSES.READY });

            expect(screen.getByRole('button', { name: 'Import' })).toBeVisible();
            fireEvent.click(screen.getByRole('button', { name: 'Import' }));

            expect(mockOnPrimaryAction).toHaveBeenCalled();
            expect(mockOnDialogDismiss).toHaveBeenCalled();
        });
    });
});
