// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { useDatasetMediaUpload } from '../../../project-dataset/hooks/dataset-media-upload';
import { UploadStatusDialogTime } from './upload-status-dialog-time.component';

jest.mock('../../../project-dataset/hooks/dataset-media-upload', () => ({
    useDatasetMediaUpload: jest.fn(),
}));

describe('UploadStatusDialogTime', () => {
    it('renders the elapsed time correctly', () => {
        const time = new Date().getTime();
        jest.mocked(useDatasetMediaUpload).mockImplementation(
            () =>
                ({
                    mediaUploadState: { timeUploadStarted: time },
                }) as ReturnType<typeof useDatasetMediaUpload>
        );

        render(<UploadStatusDialogTime />);

        expect(screen.getByText('a few seconds elapsed')).toBeInTheDocument();
    });
});
