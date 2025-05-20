// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { useDatasetStatistics } from '../../../core/statistics/hooks/use-dataset-statistics.hook';
import { useDatasetIdentifier } from '../../../pages/annotator/hooks/use-dataset-identifier.hook';
import { useMedia } from '../../../pages/media/providers/media-provider.component';
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
