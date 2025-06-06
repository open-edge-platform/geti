// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../../core/datasets/dataset.interface';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { DatasetImportDeletionDialog } from './dataset-import-deletion-dialog.component';

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

const mockTrigger = {
    isOpen: true,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

const mockOnPrimaryAction = jest.fn();
const mockOnDismiss = jest.fn();

describe(DatasetImportDeletionDialog, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should render "Delete" header, "Are you sure you want to delete "Test Dataset?"" as modal content and two action buttons "Cancel" and "Delete"', () => {
        render(
            <DatasetImportDeletionDialog
                datasetImportItem={mockDatasetImportItem}
                trigger={mockTrigger}
                onPrimaryAction={mockOnPrimaryAction}
                onDismiss={mockOnDismiss}
            />
        );

        expect(screen.getByRole('heading', { name: 'Delete' })).toBeVisible();
        expect(screen.getByText('Are you sure you want to delete "Test Dataset"?')).toBeVisible();

        expect(screen.getAllByRole('button')).toHaveLength(2);
        expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();
        expect(screen.getByRole('button', { name: 'Delete' })).toBeVisible();
    });

    it('should properly interact with "Cancel" button', () => {
        render(
            <DatasetImportDeletionDialog
                datasetImportItem={mockDatasetImportItem}
                trigger={mockTrigger}
                onPrimaryAction={mockOnPrimaryAction}
                onDismiss={mockOnDismiss}
            />
        );

        expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();
        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

        expect(mockOnDismiss).toBeCalled();
        expect(mockTrigger.close).toBeCalled();
    });

    it('should properly interact with "Delete" button', () => {
        render(
            <DatasetImportDeletionDialog
                datasetImportItem={mockDatasetImportItem}
                trigger={mockTrigger}
                onPrimaryAction={mockOnPrimaryAction}
                onDismiss={mockOnDismiss}
            />
        );

        expect(screen.getByRole('button', { name: 'Delete' })).toBeVisible();
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

        expect(mockOnDismiss).toBeCalled();
        expect(mockTrigger.close).toBeCalled();
        expect(mockOnPrimaryAction).toBeCalled();
    });

    it('should properly interact on "Esc" key press', () => {
        render(
            <DatasetImportDeletionDialog
                datasetImportItem={mockDatasetImportItem}
                trigger={mockTrigger}
                onPrimaryAction={mockOnPrimaryAction}
                onDismiss={mockOnDismiss}
            />
        );

        fireEvent.keyDown(screen.getByRole('alertdialog', { name: 'Delete' }), { key: 'Escape' });

        expect(mockOnDismiss).toBeCalled();
        expect(mockTrigger.close).toBeCalled();
    });
});
