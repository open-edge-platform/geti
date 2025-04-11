// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import { loadImageFromFile } from '../../shared/media-utils';
import { getMockedDatasetIdentifier } from '../../test-utils/mocked-items-factory/mocked-identifiers';
import { mockFile } from '../../test-utils/mockFile';
import { ErrorListItem, MEDIA_CONTENT_BUCKET, MediaUploadState, SuccessListItem } from './media-upload.interface';
import {
    computeFileUploadConcurrency,
    getElapsedTimeText,
    getIfUploadStatusBarIsVisible,
    getProcessingItems,
    getTotalProgress,
} from './utils';

jest.mock('../../shared/media-utils', () => ({
    ...jest.requireActual('../../shared/media-utils'),
    loadImageFromFile: jest.fn(),
}));

describe('media-upload-provider utils', () => {
    it('getTotalProgress', () => {
        expect(getTotalProgress(10, 90)).toEqual(10);
        expect(getTotalProgress(50, 50)).toEqual(50);
        expect(getTotalProgress(100, 0)).toEqual(100);
    });

    it('getElapsedTimeText', () => {
        expect(getElapsedTimeText(null)).toEqual('calculating...');
        expect(getElapsedTimeText(1)).toContain('elapsed');
    });

    it('getIfUploadStatusBarIsVisible', () => {
        const mockedSuccessListItem = { uploadId: '123' } as SuccessListItem;
        const mockedErrorListItem = { statusText: 'test' } as ErrorListItem;

        expect(getIfUploadStatusBarIsVisible(true, [], [])).toBe(true);
        expect(getIfUploadStatusBarIsVisible(false, [], [])).toBe(false);
        expect(getIfUploadStatusBarIsVisible(false, [mockedSuccessListItem], [])).toBe(true);
        expect(getIfUploadStatusBarIsVisible(false, [], [mockedErrorListItem])).toBe(true);
    });

    it('getProcessingItems', () => {
        const datasetId = '123321';
        const mockedMediaUploadState = {
            [datasetId]: {
                uploadProgress: {},
                isUploadInProgress: true,
                isUploadStatusBarVisible: false,
                processingQueue: [],
                waitingQueue: [],
                successList: [],
            },
        } as unknown as MediaUploadState;

        expect(
            getProcessingItems({ [datasetId]: { ...mockedMediaUploadState[datasetId], isUploadInProgress: false } })
        ).toEqual([]);

        expect(getProcessingItems(mockedMediaUploadState)).toEqual([
            {
                datasetId,
                processingQueue: [],
                waitingQueue: [],
                successList: [],
            },
        ]);
    });

    describe('computeFileUploadConcurrency', () => {
        const file8K = mockFile({ type: MEDIA_TYPE.IMAGE, size: 33177600 });
        const file4K = mockFile({ type: MEDIA_TYPE.IMAGE, size: 8294400 });
        const file = mockFile({ type: MEDIA_TYPE.IMAGE, size: 100 });
        const file4KDimensions = { width: 3840, height: 2160 };
        const file8KDimensions = { width: 7680, height: 4320 };

        it('returns correct concurrency for large files', async () => {
            const mockedImage = { ...file8KDimensions } as HTMLImageElement;
            jest.mocked(loadImageFromFile).mockResolvedValue(mockedImage);

            expect(
                await computeFileUploadConcurrency([
                    {
                        uploadId: '1',
                        meta: MEDIA_CONTENT_BUCKET.GENERIC,
                        file: file8K,
                        fileName: file8K.name,
                        fileType: file8K.type,
                        fileSize: file8K.size,
                        datasetIdentifier: getMockedDatasetIdentifier({
                            workspaceId: '1',
                            projectId: '11',
                            datasetId: '111',
                        }),
                    },
                ])
            ).toBe(1);
        });

        it('returns correct concurrency for medium files', async () => {
            const mockedImage = { ...file4KDimensions } as HTMLImageElement;
            jest.mocked(loadImageFromFile).mockResolvedValue(mockedImage);

            expect(
                await computeFileUploadConcurrency([
                    {
                        uploadId: '1',
                        meta: MEDIA_CONTENT_BUCKET.GENERIC,
                        file: file4K,
                        fileName: file4K.name,
                        fileType: file4K.type,
                        fileSize: file4K.size,
                        datasetIdentifier: getMockedDatasetIdentifier({
                            workspaceId: '1',
                            projectId: '11',
                            datasetId: '111',
                        }),
                    },
                ])
            ).toBe(5);
        });

        it('returns correct concurrency for small files', async () => {
            const mockedImage = { width: 100, height: 100 } as HTMLImageElement;
            jest.mocked(loadImageFromFile).mockResolvedValue(mockedImage);

            expect(
                await computeFileUploadConcurrency([
                    {
                        uploadId: '1',
                        meta: MEDIA_CONTENT_BUCKET.GENERIC,
                        file,
                        fileName: file.name,
                        fileType: file.type,
                        fileSize: file.size,
                        datasetIdentifier: getMockedDatasetIdentifier({
                            workspaceId: '1',
                            projectId: '11',
                            datasetId: '111',
                        }),
                    },
                ])
            ).toBe(10);
        });
    });
});
