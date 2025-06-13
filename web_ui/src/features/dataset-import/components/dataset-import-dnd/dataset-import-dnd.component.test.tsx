// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, RenderResult, screen } from '@testing-library/react';

import { IMPORT_DATASET_LEARN_MORE } from '../../../../core/const';
import { RequiredProviders } from '../../../../test-utils/required-providers-render';
import { DatasetImportDnd } from './dataset-import-dnd.component';

const mockPrepareDataset = jest.fn();
const mockSetActiveDatasetImportId = jest.fn();

const renderMockedComponent = (isAnomaly = false): RenderResult => {
    return render(
        <RequiredProviders>
            <DatasetImportDnd
                setUploadItem={mockPrepareDataset}
                setActiveUploadId={mockSetActiveDatasetImportId}
                isAnomaly={isAnomaly}
            />
        </RequiredProviders>
    );
};

describe('DatasetImportDnd', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should properly render initiated component', () => {
        renderMockedComponent();

        expect(screen.getByText('Drop the dataset .zip file here')).toBeVisible();
        expect(screen.getByRole('button', { name: /upload/i })).toBeVisible();
        expect(screen.getByText('(COCO, YOLO, VOC, Datumaro) .zip')).toBeVisible();
    });

    it('should render only a Datumaro as the supported format for anomaly projects', () => {
        renderMockedComponent(true);

        expect(screen.getByText('Drop the dataset .zip file here')).toBeVisible();
        expect(screen.getByRole('button', { name: /upload/i })).toBeVisible();
        expect(screen.getByText('(Datumaro) .zip')).toBeVisible();
    });

    it('should render "Learn more..." link to go documentation', () => {
        renderMockedComponent(true);

        expect(screen.getByText('Learn more...')).toBeVisible();
        expect(screen.getByText('Learn more...')).toHaveAttribute('href', IMPORT_DATASET_LEARN_MORE);
    });
});
