// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_TYPE } from '../../core/media/base-media.interface';
import { getMockedDatasetIdentifier } from '../../test-utils/mocked-items-factory/mocked-identifiers';
import { mockFile } from '../../test-utils/mockFile';
import { MediaUploadReducer } from './media-upload-reducer';
import { MediaUploadActionTypes } from './media-upload-reducer-actions';
import { MediaUploadItem, MediaUploadItemState, ProgressListItem, QueuedListItem } from './media-upload.interface';

const datasetId = '12';
const mockDatasetIdentifier = getMockedDatasetIdentifier({ workspaceId: '1234', projectId: '123', datasetId });
const getMockedQueuedListItem = (uploadId: string): MediaUploadItem & QueuedListItem => {
    const file = mockFile({ type: MEDIA_TYPE.IMAGE });
    return {
        type: MediaUploadItemState.QUEUED,
        uploadId,
        datasetIdentifier: mockDatasetIdentifier,
        file,
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
    };
};

const getInitialState = (list: MediaUploadItem[]) => {
    return {
        [datasetId]: {
            list,
            insufficientStorage: false,
            timeUploadStarted: null,
        },
    };
};

const mediaUploadInitialMocked = getInitialState([]);

describe('MediaUpload reducer', () => {
    it('sets common queue', () => {
        const file = mockFile({ type: MEDIA_TYPE.IMAGE });
        const waitingQueue = [
            {
                uploadId: '1',
                datasetIdentifier: mockDatasetIdentifier,
                file,
                fileName: file.name,
                fileSize: file.size,
                fileType: file.type,
                type: MediaUploadItemState.QUEUED,
            },
        ];
        const payload = { items: waitingQueue, timeUploadStarted: Date.now() };

        expect(
            MediaUploadReducer(mediaUploadInitialMocked, {
                type: MediaUploadActionTypes.ADD_TO_WAITING_QUEUE,
                payload,
                datasetId,
            })
        ).toEqual({
            ...mediaUploadInitialMocked,
            [datasetId]: {
                ...mediaUploadInitialMocked[datasetId],
                list: waitingQueue,
                timeUploadStarted: payload.timeUploadStarted,
            },
        });
    });

    it('remembers when first upload started', () => {
        const file = mockFile({ type: MEDIA_TYPE.IMAGE });
        const waitingQueue = [
            {
                uploadId: '1',
                datasetIdentifier: mockDatasetIdentifier,
                file,
                fileName: file.name,
                fileSize: file.size,
                fileType: file.type,
                type: MediaUploadItemState.QUEUED,
            },
        ];
        const payload = { items: waitingQueue, timeUploadStarted: Date.now() };

        const initialState = {
            [datasetId]: {
                list: [],
                insufficientStorage: false,
                timeUploadStarted: 100,
            },
        };

        expect(
            MediaUploadReducer(initialState, {
                type: MediaUploadActionTypes.ADD_TO_WAITING_QUEUE,
                payload,
                datasetId,
            })
        ).toEqual({
            ...initialState,
            [datasetId]: {
                ...initialState[datasetId],
                list: waitingQueue,
                timeUploadStarted: 100,
            },
        });
    });

    it('sets error list', () => {
        const list = [getMockedQueuedListItem('12345')];
        const initialState = getInitialState(list);
        const payload = {
            ...list[0],
            errors: [],
            status: 404,
            statusText: 'some error',
            type: MediaUploadItemState.ERROR,
        };

        expect(
            MediaUploadReducer(initialState, {
                type: MediaUploadActionTypes.ADD_TO_ERROR_LIST,
                payload,
                datasetId,
            })
        ).toEqual({
            ...initialState,
            [datasetId]: {
                ...initialState[datasetId],
                list: [payload],
            },
        });
    });

    it('sets success list', () => {
        const list = [getMockedQueuedListItem('12345')];
        const initialState = getInitialState(list);
        const payload = {
            ...list[0],
            type: MediaUploadItemState.SUCCESS,
        };

        expect(
            MediaUploadReducer(initialState, {
                type: MediaUploadActionTypes.ADD_TO_SUCCESS_LIST,
                payload,
                datasetId,
            })
        ).toEqual({
            ...initialState,
            [datasetId]: {
                ...mediaUploadInitialMocked[datasetId],
                list: [payload],
            },
        });
    });

    it('resets the upload list', () => {
        // TODO: Add some actual initial items
        expect(
            MediaUploadReducer(mediaUploadInitialMocked, {
                type: MediaUploadActionTypes.RESET,
                datasetId,
            })
        ).toEqual({
            ...mediaUploadInitialMocked,
            [datasetId]: {
                ...mediaUploadInitialMocked[datasetId],
                list: [],
            },
        });
    });

    it('sets insufficient storage', () => {
        const insufficientStorage = true;

        expect(
            MediaUploadReducer(mediaUploadInitialMocked, {
                type: MediaUploadActionTypes.SET_INSUFFICIENT_STORAGE,
                payload: insufficientStorage,
                datasetId,
            })
        ).toEqual({
            ...mediaUploadInitialMocked,
            [datasetId]: { ...mediaUploadInitialMocked[datasetId], insufficientStorage },
        });
    });

    it('updates media upload progress', () => {
        const uploadId = 'some-id';
        const list = [getMockedQueuedListItem(uploadId)];
        const initialState = getInitialState(list);

        const progress = {
            ...list[0],
            type: MediaUploadItemState.PROGRESS,
            progress: 30,
            uploadId,
        };

        const payload: {
            uploadId: string;
            progress: ProgressListItem;
        } = {
            uploadId,
            progress,
        };

        expect(
            MediaUploadReducer(initialState, {
                type: MediaUploadActionTypes.UPDATE_PROCESSING_ITEM,
                payload,
                datasetId,
            })
        ).toEqual({
            ...initialState,
            [datasetId]: {
                ...initialState[datasetId],
                list: [progress],
            },
        });
    });

    describe('Updating the state of an existing upload media item', () => {
        it('updates the status from queued to progress', () => {
            const uploadId = '1';
            const item = getMockedQueuedListItem(uploadId);

            const list = [getMockedQueuedListItem('0'), item, getMockedQueuedListItem('2')];

            const progress = {
                ...item,
                type: MediaUploadItemState.PROGRESS,
                progress: 30,
            };

            const mediaUploadState = {
                [datasetId]: {
                    list,
                    insufficientStorage: false,
                    timeUploadStarted: null,
                },
            };

            expect(
                MediaUploadReducer(mediaUploadState, {
                    type: MediaUploadActionTypes.UPDATE_PROCESSING_ITEM,
                    payload: { uploadId, progress },
                    datasetId,
                })
            ).toEqual({
                ...mediaUploadState,
                [datasetId]: {
                    ...mediaUploadState[datasetId],
                    list: [
                        getMockedQueuedListItem('0'),
                        { ...item, type: MediaUploadItemState.PROGRESS, progress: 30 },
                        getMockedQueuedListItem('2'),
                    ],
                },
            });
        });

        it('updates the status from progress to success', () => {
            const uploadId = '1';
            const item = getMockedQueuedListItem(uploadId);

            const list = [getMockedQueuedListItem('0'), item, getMockedQueuedListItem('2')];

            const mediaUploadState = {
                [datasetId]: {
                    list,
                    insufficientStorage: false,
                    timeUploadStarted: null,
                },
            };

            expect(
                MediaUploadReducer(mediaUploadState, {
                    type: MediaUploadActionTypes.ADD_TO_SUCCESS_LIST,
                    payload: item,
                    datasetId,
                })
            ).toEqual({
                ...mediaUploadState,
                [datasetId]: {
                    ...mediaUploadState[datasetId],
                    list: [
                        getMockedQueuedListItem('0'),
                        { ...item, type: MediaUploadItemState.SUCCESS },
                        getMockedQueuedListItem('2'),
                    ],
                },
            });
        });

        it('does not update a success item to progress', () => {
            const uploadId = '1';
            const item: MediaUploadItem & QueuedListItem = {
                ...getMockedQueuedListItem(uploadId),
                type: MediaUploadItemState.SUCCESS,
            };

            const list = [getMockedQueuedListItem('0'), item, getMockedQueuedListItem('2')];
            const progress = {
                ...item,
                progress: 98,
                type: MediaUploadItemState.PROGRESS,
            };

            const mediaUploadState = {
                [datasetId]: {
                    list,
                    insufficientStorage: false,
                    timeUploadStarted: null,
                },
            };

            expect(
                MediaUploadReducer(mediaUploadState, {
                    type: MediaUploadActionTypes.UPDATE_PROCESSING_ITEM,
                    payload: { uploadId, progress },
                    datasetId,
                })
            ).toEqual({
                ...mediaUploadState,
                [datasetId]: {
                    ...mediaUploadState[datasetId],
                    list: [
                        getMockedQueuedListItem('0'),
                        { ...item, type: MediaUploadItemState.SUCCESS },
                        getMockedQueuedListItem('2'),
                    ],
                },
            });
        });

        it('updates the status from progress to error', () => {
            const uploadId = '1';
            const item = getMockedQueuedListItem(uploadId);

            const list = [getMockedQueuedListItem('0'), item, getMockedQueuedListItem('2')];

            const mediaUploadState = {
                [datasetId]: {
                    list,
                    insufficientStorage: false,
                    timeUploadStarted: null,
                },
            };

            const errorState = { status: 2, statusText: 'Something went wrong', errors: [] };
            expect(
                MediaUploadReducer(mediaUploadState, {
                    type: MediaUploadActionTypes.ADD_TO_ERROR_LIST,
                    payload: { ...item, ...errorState },
                    datasetId,
                })
            ).toEqual({
                ...mediaUploadState,
                [datasetId]: {
                    ...mediaUploadState[datasetId],
                    list: [
                        getMockedQueuedListItem('0'),
                        { ...item, type: MediaUploadItemState.ERROR, ...errorState },
                        getMockedQueuedListItem('2'),
                    ],
                },
            });
        });

        it('updates the status from error to progress', () => {
            const uploadId = '1';
            const item = getMockedQueuedListItem(uploadId);

            const errorState = { status: 2, statusText: 'Something went wrong', errors: [] };
            const list: MediaUploadItem[] = [
                getMockedQueuedListItem('0'),
                { ...item, type: MediaUploadItemState.ERROR, ...errorState },
                getMockedQueuedListItem('2'),
            ];

            const progress = {
                ...item,
                type: MediaUploadItemState.PROGRESS,
                progress: 30,
            };

            const mediaUploadState = {
                [datasetId]: {
                    list,
                    insufficientStorage: false,
                    timeUploadStarted: null,
                },
            };

            expect(
                MediaUploadReducer(mediaUploadState, {
                    type: MediaUploadActionTypes.UPDATE_PROCESSING_ITEM,
                    payload: { uploadId, progress },
                    datasetId,
                })
            ).toEqual({
                ...mediaUploadState,
                [datasetId]: {
                    ...mediaUploadState[datasetId],
                    list: [
                        getMockedQueuedListItem('0'),
                        { ...item, type: MediaUploadItemState.PROGRESS, progress: 30 },
                        getMockedQueuedListItem('2'),
                    ],
                },
            });
        });
    });
});
