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

import { ErrorListItem, ProgressListItem, QueuedListItem, SuccessListItem } from './media-upload.interface';

export enum MediaUploadActionTypes {
    RESET = 'RESET',
    ADD_TO_WAITING_QUEUE = 'ADD_TO_WAITING_QUEUE',
    CLEAR_WAITING_QUEUE = 'CLEAR_WAITING_QUEUE',
    UPDATE_PROCESSING_ITEM = 'UPDATE_PROCESSING_ITEM',
    ADD_TO_ERROR_LIST = 'ADD_TO_ERROR_LIST',
    ADD_TO_SUCCESS_LIST = 'ADD_TO_SUCCESS_LIST',
    SET_UPLOAD_STARTED = 'SET_UPLOAD_STARTED',
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
