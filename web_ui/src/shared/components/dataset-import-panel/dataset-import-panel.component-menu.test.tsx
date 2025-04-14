// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, RenderResult, screen } from '@testing-library/react';

import { DATASET_IMPORT_STATUSES } from '../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../core/datasets/dataset.interface';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { DatasetImportPanelMenu } from './dataset-import-panel-menu.component';

const mockOnPrimaryAction = jest.fn();
const mockOnDeleteAction = jest.fn();

const mockSetActiveDatasetImportId = jest.fn();

const mockAbortDatasetImportAction = jest.fn();

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

jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: jest.fn() }),
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

const renderMockedComponent = (datasetImportItem: DatasetImportItem, isReady = false): RenderResult => {
    return render(
        <RequiredProviders>
            <DatasetImportPanelMenu
                datasetImportItem={datasetImportItem}
                datasetImportDeleteDialogTrigger={mockDatasetImportDeleteDialogTrigger}
                onPrimaryAction={mockOnPrimaryAction}
                onDeleteAction={mockOnDeleteAction}
                isReady={() => isReady}
                setActiveDatasetImportId={mockSetActiveDatasetImportId}
                abortDatasetImportAction={mockAbortDatasetImportAction}
            />
        </RequiredProviders>
    );
};

describe('DatasetImportPanelMenu', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('should display correct menu action items', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.UPLOADING },
            { status: DATASET_IMPORT_STATUSES.PREPARING },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
        ])('should display only "Cancel" action menu item when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockDatasetImportItem, status });

            expect(screen.getByLabelText('dataset-import-menu')).toBeVisible();
            fireEvent.click(screen.getByLabelText('dataset-import-menu'));

            expect(screen.getAllByLabelText('dataset-import-menu-item')).toHaveLength(1);
            expect(screen.getByLabelText('dataset-import-menu-item')).toBeVisible();
            expect(screen.getByLabelText('dataset-import-menu-item')).toHaveTextContent('Cancel');
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
        ])('should display only "Delete" action menu item when datasetImportItem status is "$status"', ({ status }) => {
            renderMockedComponent({ ...mockDatasetImportItem, status });

            expect(screen.getByLabelText('dataset-import-menu')).toBeVisible();
            fireEvent.click(screen.getByLabelText('dataset-import-menu'));

            expect(screen.getAllByLabelText('dataset-import-menu-item')).toHaveLength(1);
            expect(screen.getByLabelText('dataset-import-menu-item')).toBeVisible();
            expect(screen.getByLabelText('dataset-import-menu-item')).toHaveTextContent('Delete');
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
        ])(
            'should display "Import" and "Delete" action menu items when datasetImportItem status is "$status"',
            ({ status }) => {
                renderMockedComponent({ ...mockDatasetImportItem, status }, true);

                expect(screen.getByLabelText('dataset-import-menu')).toBeVisible();
                fireEvent.click(screen.getByLabelText('dataset-import-menu'));

                expect(screen.getAllByLabelText('dataset-import-menu-item')).toHaveLength(2);

                expect(screen.getAllByLabelText('dataset-import-menu-item')[0]).toBeVisible();
                expect(screen.getAllByLabelText('dataset-import-menu-item')[0]).toHaveTextContent('Import');

                expect(screen.getAllByLabelText('dataset-import-menu-item')[1]).toBeVisible();
                expect(screen.getAllByLabelText('dataset-import-menu-item')[1]).toHaveTextContent('Delete');
            }
        );
    });

    describe('should correct interact with menu action buttons', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });

        it('should abort dataset upload tus request by clicking "Cancel" action menu button when status is "uploading"', () => {
            renderMockedComponent({ ...mockDatasetImportItem, status: DATASET_IMPORT_STATUSES.UPLOADING });

            expect(screen.getByLabelText('dataset-import-menu')).toBeVisible();
            fireEvent.click(screen.getByLabelText('dataset-import-menu'));

            expect(screen.getAllByLabelText('dataset-import-menu-item')).toHaveLength(1);

            const menuActionButton = screen.getByLabelText('dataset-import-menu-item');
            expect(menuActionButton).toBeVisible();
            expect(menuActionButton).toHaveTextContent('Cancel');

            !!menuActionButton && fireEvent.click(menuActionButton);

            expect(mockAbortActiveUpload).toBeCalledWith(mockDatasetImportItem.id);
        });

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
        ])(
            'should abort dataset import http request by clicking "Cancel" action menu button when status is "$status"',
            ({ status }) => {
                renderMockedComponent({ ...mockDatasetImportItem, status });

                expect(screen.getByLabelText('dataset-import-menu')).toBeVisible();
                fireEvent.click(screen.getByLabelText('dataset-import-menu'));

                expect(screen.getAllByLabelText('dataset-import-menu-item')).toHaveLength(1);

                const menuActionButton = screen.getByLabelText('dataset-import-menu-item');
                expect(menuActionButton).toBeVisible();
                expect(menuActionButton).toHaveTextContent('Cancel');

                !!menuActionButton && fireEvent.click(menuActionButton);

                expect(mockAbortDatasetImportAction).toBeCalled();
            }
        );

        it.each([
            { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
            { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
            { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
            { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
        ])(
            'should open DatasetImportDeleteDialog by clicking "Delete" action menu button when status is "$status"',
            ({ status }) => {
                renderMockedComponent({ ...mockDatasetImportItem, status });

                expect(screen.getByLabelText('dataset-import-menu')).toBeVisible();
                fireEvent.click(screen.getByLabelText('dataset-import-menu'));

                expect(screen.getAllByLabelText('dataset-import-menu-item')).toHaveLength(1);

                const menuActionButton = screen.getByLabelText('dataset-import-menu-item');
                expect(menuActionButton).toBeVisible();
                expect(menuActionButton).toHaveTextContent('Delete');

                !!menuActionButton && fireEvent.click(menuActionButton);

                expect(mockDatasetImportDeleteDialogTrigger.open).toBeCalled();
            }
        );

        it.each([
            { status: DATASET_IMPORT_STATUSES.READY },
            { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
            { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
        ])(
            'should call import action (onPrimaryAction) by clicking to "Import" menu action button when status is "$status"',
            ({ status }) => {
                renderMockedComponent({ ...mockDatasetImportItem, status }, true);

                expect(screen.getByLabelText('dataset-import-menu')).toBeVisible();
                fireEvent.click(screen.getByLabelText('dataset-import-menu'));

                const menuActionButton = screen.getAllByLabelText('dataset-import-menu-item')[0];
                expect(menuActionButton).toBeVisible();
                expect(menuActionButton).toHaveTextContent('Import');

                !!menuActionButton && fireEvent.click(menuActionButton);

                expect(mockOnPrimaryAction).toBeCalled();
            }
        );
    });
});
