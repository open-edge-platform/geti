// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ErrorListItem, ProgressListItem, QueuedListItem, SuccessListItem } from './media-upload.interface';

export enum MediaUploadActionTypes {
    RESET = 'RESET',
    ADD_TO_WAITING_QUEUE = 'ADD_TO_WAITING_QUEUE',
    CLEAR_WAITING_QUEUE = 'CLEAR_WAITING_QUEUE',
    UPDATE_PROCESSING_ITEM = 'UPDATE_PROCESSING_ITEM',
    ADD_TO_ERROR_LIST = 'ADD_TO_ERROR_LIST',
    ADD_TO_SUCCESS_LIST = 'ADD_TO_SUCCESS_LIST',
    SET_INSUFFICIENT_STORAGE = 'SET_INSUFFICIENT_STORAGE',
    REMOVE_UPLOAD_STATE = 'REMOVE_UPLOAD_STATE',
    ABORT_UPLOADS = 'ABORT_UPLOADS',
}

export type DatasetMediaUploadActions =
    | {
          type: MediaUploadActionTypes.ADD_TO_WAITING_QUEUE;
          payload: {
              items: QueuedListItem[];
              timeUploadStarted: number;
          };
          datasetId: string;
      }
    | { type: MediaUploadActionTypes.ADD_TO_ERROR_LIST; payload: ErrorListItem; datasetId: string }
    | { type: MediaUploadActionTypes.ADD_TO_SUCCESS_LIST; payload: SuccessListItem; datasetId: string }
    | { type: MediaUploadActionTypes.RESET; datasetId: string }
    | { type: MediaUploadActionTypes.CLEAR_WAITING_QUEUE; datasetId: string }
    | { type: MediaUploadActionTypes.SET_INSUFFICIENT_STORAGE; payload: boolean; datasetId: string }
    | {
          type: MediaUploadActionTypes.UPDATE_PROCESSING_ITEM;
          payload: { uploadId: string; progress: ProgressListItem };
          datasetId: string;
      }
    | { type: MediaUploadActionTypes.REMOVE_UPLOAD_STATE; datasetId: string }
    | { type: MediaUploadActionTypes.ABORT_UPLOADS; datasetId: string };
