// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import {
    ErrorListItem,
    MEDIA_CONTENT_BUCKET,
    ProgressListItem,
    QueuedListItem,
    SuccessListItem,
} from '../../providers/media-upload-provider/media-upload.interface';
import { mockFile } from '../mockFile';
import { getMockedDatasetIdentifier } from './mocked-identifiers';

export const mockedMediaUploadPerDataset = {
    list: [],
    errorList: [],
    successList: [],
    waitingQueue: [],
    processingQueue: [],
    progressMap: {},
    uploadProgress: {},
    timeUploadStarted: null,
    insufficientStorage: false,
    isUploadInProgress: false,
    isUploadStatusBarVisible: false,
    abortControllers: [],
};

export const mockedListItem = (fileName: string): QueuedListItem => {
    const file = mockFile({ type: MEDIA_TYPE.IMAGE, name: fileName });
    return {
        uploadId: '1',
        meta: MEDIA_CONTENT_BUCKET.GENERIC,
        file,
        fileName: file.name,
        fileType: file.type,
        fileSize: file.size,
        datasetIdentifier: getMockedDatasetIdentifier({ workspaceId: '1', projectId: '11', datasetId: '111' }),
    };
};

export const getMockedSuccessListItem = (fileName: string, uploadId = '123'): SuccessListItem => ({
    ...mockedListItem(fileName),
    uploadId,
});

export const getMockedProgressListItem = (fileName: string, uploadId = '123', progress = 0): ProgressListItem => ({
    ...mockedListItem(fileName),
    uploadId,
    progress,
});

export const getMockedErrorListItem = (fileName: string): ErrorListItem => ({
    ...mockedListItem(fileName),
    uploadId: '',
    errors: [],
    status: 0,
    statusText: '',
});
