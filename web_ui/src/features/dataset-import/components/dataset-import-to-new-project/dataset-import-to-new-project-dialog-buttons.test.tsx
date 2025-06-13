// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';

import {
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TASK_TYPE,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
} from '../../../../core/datasets/dataset.enum';
import { DatasetImportToNewProjectItem } from '../../../../core/datasets/dataset.interface';
import { getMockedDatasetImportItem } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { DatasetImportToNewProjectDialogButtons } from './dataset-import-to-new-project-dialog-buttons.component';

const mockedDatasetImportItem = getMockedDatasetImportItem({});

const mockDeletionDialogTrigger = {
    isOpen: false,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

const mockPatchDatasetImport = jest.fn();
const mockOnPrimaryAction = jest.fn();
const mockOnDialogDismiss = jest.fn();

const mockAbortDatasetImportAction = jest.fn();
const mockDeleteTemporallyDatasetImport = jest.fn();

let mockIsReadyValue = false;

const mockAbortActiveUpload = jest.fn();
jest.mock('../../../../providers/tus-upload-provider/tus-upload-provider.component', () => ({
    ...jest.requireActual('../../../../providers/tus-upload-provider/tus-upload-provider.component'),
    useTusUpload: () => ({ abortActiveUpload: mockAbortActiveUpload }),
}));

const renderMockedComponent = (datasetImportItem: DatasetImportToNewProjectItem | undefined) =>
    render(
        <DatasetImportToNewProjectDialogButtons
            isReady={() => mockIsReadyValue}
            deletionDialogTrigger={mockDeletionDialogTrigger}
            datasetImportItem={datasetImportItem}
            patchDatasetImport={mockPatchDatasetImport}
            onPrimaryAction={mockOnPrimaryAction}
            onDialogDismiss={mockOnDialogDismiss}
            abortDatasetImportAction={mockAbortDatasetImportAction}
            deleteTemporallyDatasetImport={mockDeleteTemporallyDatasetImport}
        />
    );

describe(DatasetImportToNewProjectDialogButtons, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('should properly render buttons depending on datasetImportItem statusand active step', () => {
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
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
        ])('should show "Hide" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockedDatasetImportItem, status });

            expect(screen.getByRole('button', { name: 'Hide' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
        ])('should show "Cancel" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockedDatasetImportItem, status });

            expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
        ])('should hide "Cancel" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockedDatasetImportItem, status });
            expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
        ])('should show "Delete" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockedDatasetImportItem, status });

            expect(screen.getByRole('button', { name: 'Delete' })).toBeVisible();
        });

        it('should hide "Delete" button when there is no datasetImportItem', () => {
            renderMockedComponent(undefined);

            expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
        ])('should hide "Delete" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockedDatasetImportItem, status });

            expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
        });

        it('should show "Back" button when the previous step available', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN,
            });
            expect(screen.getByRole('button', { name: 'Back' })).toBeVisible();
        });

        it('should hide "Back" button when there is no previous step available', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
            });

            expect(screen.queryByRole('button', { name: 'Back' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
        ])('should show "Back" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN,
                status,
            });
            expect(screen.getByRole('button', { name: 'Back' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
        ])('should hide "Back" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockedDatasetImportItem, status });

            expect(screen.queryByRole('button', { name: 'Back' })).not.toBeInTheDocument();
        });

        it('should show "Next" button when the next step available', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
            });

            expect(screen.getByRole('button', { name: 'Next' })).toBeVisible();
        });

        it('should hide "Next" button when there is no next step available', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
            });

            expect(screen.queryByRole('button', { name: 'Next' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
        ])('should show "Next" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN,
                status,
            });

            expect(screen.getByRole('button', { name: 'Next' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
        ])('should hide "Next" button when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockedDatasetImportItem, status });

            expect(screen.queryByRole('button', { name: 'Next' })).not.toBeInTheDocument();
        });

        it('should show "Create" button when the active step is "labels"', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
            });

            expect(screen.getByRole('button', { name: 'Create' })).toBeVisible();
        });

        it('should hide "Create" button when the active step is "dataset"', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
            });

            expect(screen.queryByRole('button', { name: 'Create' })).not.toBeInTheDocument();
        });

        it('should hide "Create" button when the active step is "domain"', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN,
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
            });

            expect(screen.queryByRole('button', { name: 'Create' })).not.toBeInTheDocument();
        });

        it('should disable "Create" button when datasetImportItem is not ready', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
            });

            expect(screen.queryByRole('button', { name: 'Create' })).toHaveAttribute('disabled');
        });
    });

    describe('should properly interact on each button click', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it('should call dialog dismiss on click to "Hide" button', () => {
            renderMockedComponent(mockedDatasetImportItem);

            expect(screen.getByRole('button', { name: 'Hide' })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: 'Hide' }));
            expect(mockOnDialogDismiss).toHaveBeenCalled();
        });

        it('should abort tus upload request and remove activeDatasetImportItem on click to "Cancel" button', async () => {
            mockAbortActiveUpload.mockResolvedValue(true);

            renderMockedComponent({ ...mockedDatasetImportItem, status: DATASET_IMPORT_STATUSES.UPLOADING });

            expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

            await waitFor(() => {
                expect(mockAbortActiveUpload).toHaveBeenCalledWith('987-654-321');
                expect(mockDeleteTemporallyDatasetImport).toHaveBeenCalled();
            });
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
        ])(
            'should abort $status http request and remove activeDatasetImportItem on click to "Cancel" button',
            ({ status }) => {
                renderMockedComponent({ ...mockedDatasetImportItem, status });

                expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();

                fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
                expect(mockAbortDatasetImportAction).toHaveBeenCalledWith('192-837-465');
                expect(mockDeleteTemporallyDatasetImport).toHaveBeenCalled();
            }
        );

        it('should open deletion dialog on click to "Delete" button', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
            });

            expect(screen.getByRole('button', { name: 'Delete' })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

            expect(mockDeletionDialogTrigger.open).toHaveBeenCalled();
        });

        it('should step back on click to "Back" button', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN,
            });

            expect(screen.getByRole('button', { name: 'Back' })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: 'Back' }));

            expect(mockPatchDatasetImport).toHaveBeenCalledWith({ activeStep: 'dataset', id: '987-654-321' });
        });

        it('should go to the next step on click to "Next" button', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                supportedProjectTypes: [
                    {
                        projectType: 'segmentation',
                        pipeline: {
                            connections: [
                                {
                                    from: 'dataset_0',
                                    to: 'detection_1',
                                },
                            ],
                            tasks: [
                                {
                                    title: 'dataset_0',
                                    taskType: DATASET_IMPORT_TASK_TYPE.DATASET,
                                    labels: [],
                                },
                                {
                                    title: 'detection_1',
                                    taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                                    labels: [
                                        {
                                            name: 'det',
                                            group: 'Detection labels',
                                        },
                                    ],
                                },
                            ],
                        },
                    },
                ],
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
            });

            expect(screen.getByRole('button', { name: 'Next' })).toBeVisible();
            fireEvent.click(screen.getByRole('button', { name: 'Next' }));

            expect(mockPatchDatasetImport).toHaveBeenCalledWith({
                activeStep: 'domain',
                completedSteps: ['dataset'],
                id: '987-654-321',
                openedSteps: ['domain'],
                status: 'taskTypeSelectionToNewProject',
            });
        });

        it('should call onPrimaryAction and onDialogDismiss on click to "Create" button', () => {
            mockIsReadyValue = true;

            renderMockedComponent({
                ...mockedDatasetImportItem,
                labels: [getMockedLabel()],
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
            });

            expect(screen.getByRole('button', { name: 'Create' })).toBeVisible();
            fireEvent.click(screen.getByRole('button', { name: 'Create' }));

            expect(mockOnPrimaryAction).toHaveBeenCalled();
            expect(mockOnDialogDismiss).toHaveBeenCalled();
        });

        it('"Create" button should be disabled on the labels step if the "ready" conditions are not met', () => {
            mockIsReadyValue = false;

            renderMockedComponent({
                ...mockedDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
            });

            expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();
        });

        it('If there are no selected labels, a warning message should be shown', () => {
            mockIsReadyValue = false;

            renderMockedComponent({
                ...mockedDatasetImportItem,
                labels: [],
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
            });

            expect(screen.getByText('Please select at least 1 label')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();
        });

        it('If there is only 1 label select on a classification project, a warning should be shown', () => {
            mockIsReadyValue = false;

            renderMockedComponent({
                ...mockedDatasetImportItem,
                labels: [getMockedLabel()],
                taskType: DATASET_IMPORT_TASK_TYPE.CLASSIFICATION,
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
            });

            expect(screen.getByText('Classification projects require at least 2 top level labels')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();
        });

        it('If the import item has no suppported task types, "Next" button should be disabled', () => {
            renderMockedComponent({
                ...mockedDatasetImportItem,
                labels: [getMockedLabel()],
                supportedProjectTypes: [],
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
            });

            expect(screen.getByRole('button', { name: /Next/ })).toBeDisabled();
        });
    });
});
