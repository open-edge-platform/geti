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
