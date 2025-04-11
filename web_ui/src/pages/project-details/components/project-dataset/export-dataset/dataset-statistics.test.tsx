// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen } from '@testing-library/react';

import { useDatasetStatistics } from '../../../../../core/statistics/hooks/use-dataset-statistics.hook';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { useMedia } from '../../../../media/providers/media-provider.component';
import { ExportDatasetStatistics } from './export-dataset-dialog.component';

jest.mock('../../../../media/providers/media-provider.component', () => ({
    useMedia: jest.fn(),
}));

jest.mock('../../../../annotator/hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: jest.fn(),
}));

jest.mock('../../../../../core/statistics/hooks/use-dataset-statistics.hook', () => ({
    useDatasetStatistics: jest.fn(),
}));

describe('ExportDatasetStatistics', () => {
    const mockUseMedia = useMedia as jest.Mock;
    const mockUseDatasetIdentifier = useDatasetIdentifier as jest.Mock;
    const mockUseDatasetStatistics = useDatasetStatistics as jest.Mock;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders total images and videos correctly', () => {
        mockUseMedia.mockReturnValue({ totalVideos: 5, totalImages: 10 });
        mockUseDatasetIdentifier.mockReturnValue({
            organizationId: 'org1',
            workspaceId: 'ws1',
            projectId: 'proj1',
            datasetId: 'ds1',
        });
        mockUseDatasetStatistics.mockReturnValue({
            useGetAllTaskDatasetStatistics: () => ({
                data: { overview: { annotatedImages: 8, annotatedFrames: 3 } },
            }),
        });

        render(<ExportDatasetStatistics />);

        expect(screen.getByText(/Total: 10 images, 5 videos/)).toBeInTheDocument();
        expect(screen.getByText(/Annotated: 8 images, 3 frames/)).toBeInTheDocument();
    });

    it('renders total images correctly when there are no videos', () => {
        mockUseMedia.mockReturnValue({ totalVideos: 0, totalImages: 10 });
        mockUseDatasetIdentifier.mockReturnValue({
            organizationId: 'org1',
            workspaceId: 'ws1',
            projectId: 'proj1',
            datasetId: 'ds1',
        });
        mockUseDatasetStatistics.mockReturnValue({
            useGetAllTaskDatasetStatistics: () => ({
                data: { overview: { annotatedImages: 8, annotatedFrames: 0 } },
            }),
        });

        render(<ExportDatasetStatistics />);

        expect(screen.getByText(/Total: 10 images/)).toBeInTheDocument();
        expect(screen.getByText(/Annotated: 8 images/)).toBeInTheDocument();
        expect(screen.queryByText(/video/)).not.toBeInTheDocument();
        expect(screen.queryByText(/frame/)).not.toBeInTheDocument();
    });
});
