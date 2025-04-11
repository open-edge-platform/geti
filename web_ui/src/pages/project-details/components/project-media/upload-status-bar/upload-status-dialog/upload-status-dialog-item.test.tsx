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

import { ComponentProps } from 'react';

import { screen } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../../../core/media/base-media.interface';
import { MediaUploadProvider } from '../../../../../../providers/media-upload-provider/media-upload-provider.component';
import {
    ErrorListItem,
    ProgressListItem,
    SuccessListItem,
} from '../../../../../../providers/media-upload-provider/media-upload.interface';
import { getMockedDatasetIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { mockFile } from '../../../../../../test-utils/mockFile';
import { projectRender } from '../../../../../../test-utils/project-provider-render';
import { UploadStatusDialogItem, UploadStatusDialogItemTypes } from './upload-status-dialog-item.component';

const render = async ({ item, type }: ComponentProps<typeof UploadStatusDialogItem>) => {
    return projectRender(
        <MediaUploadProvider>
            <UploadStatusDialogItem item={item} type={type} />
        </MediaUploadProvider>
    );
};

describe('UploadStatusDialogItem', () => {
    describe('renders the correct file type icon', () => {
        const item = {
            datasetIdentifier: getMockedDatasetIdentifier({ workspaceId: '1', projectId: '11', datasetId: '111' }),
            uploadId: '1234',
        };

        it('for images', async () => {
            const file = mockFile({ type: MEDIA_TYPE.IMAGE });
            const mockItem = {
                ...item,
                file,
                fileName: file.name,
                fileType: file.type,
                fileSize: file.size,
            };

            const { container } = await render({ item: mockItem, type: UploadStatusDialogItemTypes.SUCCESS });

            const icon = container.querySelector('svg');

            expect(icon?.getAttribute('aria-label')).toEqual('image-icon');
        });

        it('for videos', async () => {
            const file = mockFile({ type: MEDIA_TYPE.VIDEO });
            const mockItem = {
                ...item,
                file,
                fileName: file.name,
                fileType: file.type,
                fileSize: file.size,
            };

            const { container } = await render({ item: mockItem, type: UploadStatusDialogItemTypes.SUCCESS });

            const icon = container.querySelector('svg');

            expect(icon?.getAttribute('aria-label')).toEqual('play-icon');
        });

        it('for unknown file types', async () => {
            const file = mockFile({ type: 'plain/txt' });
            const mockItem = {
                ...item,
                file,
                fileName: file.name,
                fileType: file.type,
                fileSize: file.size,
            };

            await render({ item: mockItem, type: UploadStatusDialogItemTypes.SUCCESS });

            expect(screen.getByLabelText('alert-circle-icon')).toBeInTheDocument();
        });
    });

    it('renders the correct icons and styles for SUCCESS type', async () => {
        const file = mockFile({ type: MEDIA_TYPE.IMAGE });
        const mockSuccessItem: SuccessListItem = {
            datasetIdentifier: getMockedDatasetIdentifier({ workspaceId: '1', projectId: '11', datasetId: '111' }),
            fileName: file.name,
            fileType: file.type,
            fileSize: file.size,
            uploadId: '1234',
        };

        const { container } = await render({ item: mockSuccessItem, type: UploadStatusDialogItemTypes.SUCCESS });

        // Check the suffix icon (second svg)
        const icons = container.querySelectorAll('svg');

        expect(icons[1].getAttribute('aria-label')).toEqual('upload-success-icon');

        // Check the ThinProgressBar styles
        expect(screen.getByTestId('thin-progress-bar')).toHaveStyle({
            backgroundColor: 'positive',
        });
    });

    it('renders the correct icons and styles for PROGRESS type', async () => {
        const file = mockFile({ type: MEDIA_TYPE.IMAGE });
        const mockProgressItem: ProgressListItem = {
            datasetIdentifier: getMockedDatasetIdentifier({ workspaceId: '1', projectId: '11', datasetId: '111' }),
            file,
            fileName: file.name,
            fileType: file.type,
            fileSize: file.size,
            uploadId: '1234',
            progress: 50,
        };

        await render({ item: mockProgressItem, type: UploadStatusDialogItemTypes.PROGRESS });

        // Check the suffix icon (second svg)
        expect(screen.getByLabelText('Loading...')).toBeInTheDocument();

        // Check the ThinProgressBar styles
        expect(screen.getByTestId('thin-progress-bar')).toHaveStyle({
            backgroundColor: 'informative',
        });
    });

    it('renders the correct icons and styles for ERROR type', async () => {
        const file = mockFile({ type: MEDIA_TYPE.IMAGE });
        const mockErrorItem: ErrorListItem = {
            datasetIdentifier: getMockedDatasetIdentifier({ workspaceId: '1', projectId: '11', datasetId: '111' }),
            file,
            fileName: file.name,
            fileType: file.type,
            fileSize: file.size,
            uploadId: '1234',
            errors: [],
            status: 400,
            statusText: 'some error',
        };

        const { container } = await render({ item: mockErrorItem, type: UploadStatusDialogItemTypes.ERROR });

        // Check the suffix icon (second svg)
        const icons = container.querySelectorAll('svg');

        expect(icons[1].getAttribute('aria-label')).toEqual('alert-icon');

        // Check the ThinProgressBar styles
        expect(screen.getByTestId('thin-progress-bar')).toHaveStyle({
            backgroundColor: 'negative',
        });
    });
});
