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

import { DatasetMediaUploadActions, MediaUploadActionTypes } from './media-upload-reducer-actions';
import { MediaUploadItem, MediaUploadItemState, MediaUploadPerDataset, QueuedListItem } from './media-upload.interface';

export const getInitialStatePerDataset = (): MediaUploadPerDataset => {
    const initialState = {
        uploadProgress: {},
        waitingQueue: [],
        processingQueue: [],
        errorList: [],
        successList: [],
        progressMap: {},
        list: [],

        insufficientStorage: false,
        timeUploadStarted: null,
        isUploadStatusBarVisible: false,
        isUploadInProgress: false,
    };

    return initialState;
};

// Update the provided new item in the list or add it if it is not part of the list
const setItem = (list: MediaUploadItem[], newItem: MediaUploadItem) => {
    const newItemIndex = list.findIndex((item) => item.uploadId === newItem.uploadId);

    const newList = Array.from(list);
    if (newItemIndex >= 0) {
        if (newList[newItemIndex].type === MediaUploadItemState.SUCCESS) {
            return newList;
        }

        newList[newItemIndex] = newItem;
    } else if (newItem.type === MediaUploadItemState.QUEUED) {
        newList.push(newItem);
    }

    return newList;
};
interface MediaUploadReducerStatePerDataset {
    list: MediaUploadItem[];
    timeUploadStarted: number | null;
    insufficientStorage: boolean;
}

type MediaUploadReducerState = Record<string /* dataset id */, MediaUploadReducerStatePerDataset>;

export const MediaUploadReducer = (
    state: MediaUploadReducerState,
    action: DatasetMediaUploadActions
): MediaUploadReducerState => {
    const stateOfCurrentDataset = state[action.datasetId] ?? {
        list: [],
        insufficientStorage: false,
        timeUploadStarted: null,
    };

    switch (action.type) {
        case MediaUploadActionTypes.ADD_TO_WAITING_QUEUE: {
            const { payload, datasetId } = action;
            const { items } = payload;

            const list: MediaUploadItem[] = [
                ...stateOfCurrentDataset.list,
                ...items.map((item: QueuedListItem) => ({ ...item, type: MediaUploadItemState.QUEUED as const })),
            ];

            return {
                ...state,
                [datasetId]: {
                    ...stateOfCurrentDataset,
                    list,
                    timeUploadStarted: stateOfCurrentDataset.timeUploadStarted ?? payload.timeUploadStarted,
                },
            };
        }
        // The below 3 actions could be combined into a single "UPDATE_ITEM" action...
        case MediaUploadActionTypes.UPDATE_PROCESSING_ITEM: {
            const { payload, datasetId } = action;

            const newList = setItem(stateOfCurrentDataset.list, {
                ...payload.progress,
                type: MediaUploadItemState.PROGRESS,
            });

            return {
                ...state,
                [datasetId]: { ...stateOfCurrentDataset, list: newList },
            };
        }
        case MediaUploadActionTypes.ADD_TO_ERROR_LIST: {
            const { payload, datasetId } = action;

            const newList = setItem(stateOfCurrentDataset.list, { ...payload, type: MediaUploadItemState.ERROR });

            return {
                ...state,
                [datasetId]: { ...stateOfCurrentDataset, list: newList },
            };
        }
        case MediaUploadActionTypes.ADD_TO_SUCCESS_LIST: {
            const { payload, datasetId } = action;

            const newList = setItem(stateOfCurrentDataset.list, { ...payload, type: MediaUploadItemState.SUCCESS });

            return {
                ...state,
                [datasetId]: { ...stateOfCurrentDataset, list: newList },
            };
        }
        case MediaUploadActionTypes.RESET: {
            const { datasetId } = action;

            return {
                ...state,
                [datasetId]: { ...stateOfCurrentDataset, list: [] },
            };
        }
        case MediaUploadActionTypes.CLEAR_WAITING_QUEUE: {
            const { datasetId } = action;

            const newList = stateOfCurrentDataset.list.filter((item) => item.type !== MediaUploadItemState.QUEUED);

            return {
                ...state,
                [datasetId]: { ...stateOfCurrentDataset, list: newList },
            };
        }
        // TODO This could be removed or put in a globalish state
        case MediaUploadActionTypes.SET_INSUFFICIENT_STORAGE: {
            const { payload: isInsufficientStorage, datasetId } = action;

            return {
                ...state,
                [datasetId]: { ...stateOfCurrentDataset, insufficientStorage: isInsufficientStorage },
            };
        }
        case MediaUploadActionTypes.REMOVE_UPLOAD_STATE: {
            const { datasetId } = action;

            if (stateOfCurrentDataset === undefined) {
                return state;
            }

            const copyState = { ...state };

            delete copyState[datasetId];

            return copyState;
        }
        case MediaUploadActionTypes.ABORT_UPLOADS: {
            const { datasetId } = action;

            const newList = stateOfCurrentDataset.list.filter(
                (item) => item.type !== MediaUploadItemState.QUEUED && item.type !== MediaUploadItemState.PROGRESS
            );

            return {
                ...state,
                [datasetId]: { ...stateOfCurrentDataset, list: newList },
            };
        }
        default:
            return state;
    }
};
