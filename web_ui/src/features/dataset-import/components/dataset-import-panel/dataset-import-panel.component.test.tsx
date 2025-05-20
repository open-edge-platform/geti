// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, RenderResult, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DATASET_IMPORT_MESSAGE } from '../../../../core/datasets/dataset.const';
import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../../core/datasets/dataset.interface';
import { DatasetImportService } from '../../../../core/datasets/services/dataset.interface';
import { createInMemoryDatasetImportService } from '../../../../core/datasets/services/in-memory-dataset-import-service';
import { JobStepState } from '../../../../core/jobs/jobs.const';
import {
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
} from '../../../../core/jobs/jobs.interface';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { ProjectProvider } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImportStatusJob, getMockedPrepareJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { DatasetImportPanel, FILE_FORMAT_ERROR_MESSAGE } from './dataset-import-panel.component';

const mockOnPrimaryAction = jest.fn();
const mockOnDeleteAction = jest.fn();

const mockPrepareDataset = jest.fn();
const mockPrepareDatasetAction = jest.fn();
const mockSetActiveDatasetImportId = jest.fn();

const mockAbortDatasetImportAction = jest.fn();

const mockDatasetImportDialogTrigger = {
    isOpen: false,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

const mockDatasetImportDeleteDialogTrigger = {
    isOpen: false,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

const mockDatasetImportItem: DatasetImportItem = {
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
};

const mockedAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockedAddNotification }),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ datasetId: 'dataset-id' }),
}));

const mockAbortActiveUpload = jest.fn();
jest.mock('../../../providers/tus-upload-provider/tus-upload-provider.component', () => ({
    ...jest.requireActual('../../../providers/tus-upload-provider/tus-upload-provider.component'),
    useTusUpload: () => ({ abortActiveUpload: mockAbortActiveUpload }),
}));

const renderMockedComponent = async ({
    datasetImportItem = mockDatasetImportItem,
    datasetImportService = createInMemoryDatasetImportService(),
}: {
    datasetImportItem?: DatasetImportItem;
    datasetImportService?: DatasetImportService;
} = {}): Promise<RenderResult> => {
    const component = providersRender(
        <ProjectProvider
            projectIdentifier={getMockedProjectIdentifier({
                projectId: 'project-id',
                workspaceId: 'workspace-id',
            })}
        >
            <DatasetImportPanel
                datasetImportItem={datasetImportItem}
                datasetImportDialogTrigger={mockDatasetImportDialogTrigger}
                datasetImportDeleteDialogTrigger={mockDatasetImportDeleteDialogTrigger}
                onPrimaryAction={mockOnPrimaryAction}
                onDeleteAction={mockOnDeleteAction}
                isReady={() => false}
                prepareDataset={mockPrepareDataset}
                prepareDatasetAction={mockPrepareDatasetAction}
                setActiveDatasetImportId={mockSetActiveDatasetImportId}
                abortDatasetImportAction={mockAbortDatasetImportAction}
            />
        </ProjectProvider>,
        { services: { datasetImportService } }
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return component;
};

describe('DatasetImportPanel', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should properly render initiated component', async () => {
        await renderMockedComponent();

        expect(screen.getByText('Import dataset - Test Dataset (1Gb)')).toBeVisible();
        expect(screen.getByRole('progressbar')).toBeVisible();
        expect(screen.getByText('Uploading...')).toBeVisible();
        expect(screen.getByText('50%')).toBeVisible();
        expect(screen.getByText('500Mb')).toBeVisible();
        expect(screen.getByText('10 minutes')).toBeVisible();
        expect(screen.getByText('See details')).toBeVisible();
        expect(screen.getByTestId('thin-progress-bar')).toHaveStyle({ width: '50%' });
    });

    it('should show message from the job while preparing dataset to be imported', async () => {
        const datasetImportItem: DatasetImportItem = {
            ...mockDatasetImportItem,
            preparingJobId: '123-456-789',
            status: DATASET_IMPORT_STATUSES.PREPARING,
        };

        const datasetImportService = createInMemoryDatasetImportService();
        const mockedStep = {
            message: 'Dataset is parsed successfully',
            index: 1,
            progress: 100,
            state: JobStepState.RUNNING,
            stepName: 'Prepare dataset import to new project',
        };
        datasetImportService.prepareDatasetImportNewProjectJob = jest.fn(() =>
            Promise.resolve(
                getMockedPrepareJob({
                    steps: [mockedStep],
                }) as JobPrepareDatasetImportNewProjectStatus
            )
        );

        await renderMockedComponent({
            datasetImportItem,
            datasetImportService,
        });

        expect(await screen.findByText(`${mockedStep.stepName}: ${mockedStep.message}`)).toBeVisible();
    });

    it('should show message from the job while importing dataset', async () => {
        const datasetImportItem: DatasetImportItem = {
            ...mockDatasetImportItem,
            importingJobId: '987-654-321',
            status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
        };

        const datasetImportService = createInMemoryDatasetImportService();
        const mockedStep = {
            message: 'Project created and populated successfully',
            index: 1,
            progress: 100,
            state: JobStepState.RUNNING,
            stepName: 'Create project from import dataset',
        };
        datasetImportService.importDatasetToNewProjectStatusJob = jest.fn(() =>
            Promise.resolve(
                getMockedImportStatusJob({
                    steps: [mockedStep],
                }) as JobImportDatasetToNewProjectStatus
            )
        );

        await renderMockedComponent({
            datasetImportItem,
            datasetImportService,
        });

        expect(await screen.findByText(`${mockedStep.stepName}: ${mockedStep.message}`)).toBeVisible();
    });

    it('shows file format error', async () => {
        await renderMockedComponent({
            datasetImportItem: { ...mockDatasetImportItem, status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
        });

        const getFileInput = () => screen.getByLabelText('file-input');

        expect(getFileInput()).toBeInTheDocument();

        const file = new File(['some-content'], 'dataset.zip', { type: 'file/zip' });

        mockSetActiveDatasetImportId.mockImplementationOnce(() => {
            throw new Error('Test error');
        });

        await userEvent.upload(getFileInput(), file);

        expect(mockedAddNotification).toHaveBeenCalledWith({
            message: FILE_FORMAT_ERROR_MESSAGE,
            type: NOTIFICATION_TYPE.ERROR,
        });
    });

    describe('should display correct datasetImportItem status', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it.each([
            {
                status: DATASET_IMPORT_STATUSES.UPLOADING,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.UPLOADING],
            },
            {
                status: DATASET_IMPORT_STATUSES.PREPARING,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.PREPARING],
            },
            {
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT],
            },
            {
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT],
            },
        ])(
            'should display CircleLoader icon and "$message" text when datasetImportItem status is "$status"',
            async ({ status, message }) => {
                await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });

                expect(screen.getByRole('progressbar')).toBeVisible();
                expect(screen.getByText(message)).toBeVisible();
            }
        );

        it.each([
            {
                iconClass: 'negative',
                status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.IMPORTING_ERROR],
            },
            {
                iconClass: 'negative',
                status: DATASET_IMPORT_STATUSES.PREPARING_ERROR,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.PREPARING_ERROR],
            },
            {
                iconClass: 'negative',
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR],
            },
            {
                iconClass: 'negative',
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR],
            },
        ])(
            'should display Alert icon ($iconClass) and "$message" text when datasetImportItem status is "$status"',
            async ({ status, message, iconClass }) => {
                await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });

                expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();

                expect(screen.getByTestId('alert-icon')).toBeVisible();
                expect(screen.getByTestId('alert-icon')).toHaveClass(iconClass);
                expect(screen.getByText(message)).toBeVisible();
            }
        );

        it.each([
            {
                status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED],
            },
            {
                status: DATASET_IMPORT_STATUSES.READY,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.READY],
            },
            {
                status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT],
            },
            {
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT],
            },
            {
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
                message: DATASET_IMPORT_MESSAGE[DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT],
            },
        ])(
            'should display Info icon and "$message" text when datasetImportItem status is "$status"',
            async ({ status, message }) => {
                await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });

                expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();

                expect(screen.getByTestId('info-icon')).toBeVisible();
                expect(screen.getByText(message)).toBeVisible();
            }
        );
    });

    describe('should display correct action button', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it('should display "Map labels" button when datasetImportItem status is "labelsMappingToExistingProject"', async () => {
            await renderMockedComponent({
                datasetImportItem: {
                    ...mockDatasetImportItem,
                    status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
                },
            });
            expect(screen.getByRole('button', { name: 'Map labels' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
            { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
        ])('should not display "See details" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });
            expect(screen.queryByRole('button', { name: 'See details' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
        ])('should display "See details" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });
            expect(screen.getByRole('button', { name: 'See details' })).toBeVisible();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
            { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
        ])('should not display "Try again" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });
            expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
        ])('should display "Try again" button when datasetImportItem status is "$status"', async ({ status }) => {
            await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });
            expect(screen.getByRole('button', { name: 'Try again' })).toBeVisible();
        });
    });

    describe('should correct interact with action buttons', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it('should open DatasetImportDialog by clicking to "Map labels" action button when status is "labelsMappingToExistingProject"', async () => {
            await renderMockedComponent({
                datasetImportItem: {
                    ...mockDatasetImportItem,
                    status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
                },
            });
            const actionButton = screen.getByRole('button', { name: 'Map labels' });
            expect(actionButton).toBeVisible();
            !!actionButton && fireEvent.click(actionButton);
            expect(mockDatasetImportDialogTrigger.open).toHaveBeenCalled();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
        ])(
            'should open DatasetImportDialog by clicking to "See details" action button when status is "$status"',
            async ({ status }) => {
                await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });

                const actionButton = screen.getByRole('button', { name: 'See details' });
                expect(actionButton).toBeVisible();
                !!actionButton && fireEvent.click(actionButton);
                expect(mockDatasetImportDialogTrigger.open).toHaveBeenCalled();
            }
        );

        it('should call prepareDatasetAction by clicking to "Try again" action button when status is "preparingError"', async () => {
            await renderMockedComponent({
                datasetImportItem: { ...mockDatasetImportItem, status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            });
            const actionButton = screen.getByRole('button', { name: 'Try again' });
            expect(actionButton).toBeVisible();
            !!actionButton && fireEvent.click(actionButton);
            expect(mockPrepareDatasetAction).toHaveBeenCalledWith(
                mockDatasetImportItem.id,
                mockDatasetImportItem.uploadId
            );
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
        ])(
            'should open open file native modal by clicking to "Try again" action button when status is "$status"',
            async ({ status }) => {
                await renderMockedComponent({ datasetImportItem: { ...mockDatasetImportItem, status } });

                const getFileInput = () => screen.getByLabelText('file-input');

                expect(getFileInput()).toBeInTheDocument();

                const file = new File(['some-content'], 'dataset.zip', { type: 'file/zip' });

                await userEvent.upload(getFileInput(), file);

                expect(mockPrepareDataset).toHaveBeenCalledWith(file, 'dataset-id');
                expect(mockSetActiveDatasetImportId).toHaveBeenCalled();
            }
        );
    });
});
