// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, RenderResult, screen } from '@testing-library/react';

import { IMPORT_DATASET_LEARN_MORE } from '../../../core/const';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
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
