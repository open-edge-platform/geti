// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
