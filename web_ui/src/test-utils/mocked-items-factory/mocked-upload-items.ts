// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import {
    ErrorListItem,
    MEDIA_CONTENT_BUCKET,
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

export const getMockedErrorListItem = (fileName: string): ErrorListItem => ({
    ...mockedListItem(fileName),
    uploadId: '',
    errors: [],
    status: 0,
    statusText: '',
});
