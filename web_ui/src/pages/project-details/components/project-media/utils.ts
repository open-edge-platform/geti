// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import {
    MEDIA_CONTENT_BUCKET,
    UploadProgress,
} from '../../../../providers/media-upload-provider/media-upload.interface';

export const MIN_NUMBER_OF_NORMAL_REQUIRED_MEDIA_ITEMS = 12;
export const MIN_NUMBER_OF_ANOMALOUS_REQUIRED_MEDIA_ITEMS = 3;

export const SELECT_ALL_LABEL = 'Select all media';
export const DELETE_SELECTED_MEDIA_LABEL = 'Delete selected media';
export const SEARCH_MEDIA_LABEL = 'Search media by name (regex allowed)';
export const FILTER_MEDIA_LABEL = 'Filter media';
export const SORT_MEDIA_LABEL = 'Sort media';
export const UPLOAD_MEDIA_LABEL = 'Upload media';

export const getUploadingStatePerBucket = (uploadProgress: UploadProgress, bucket: MEDIA_CONTENT_BUCKET): boolean => {
    return uploadProgress[bucket]?.isUploading ?? false;
};
