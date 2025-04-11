// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useCallback, useMemo } from 'react';

import { useMediaUpload } from '../../../../../providers/media-upload-provider/media-upload-provider.component';
import { getInitialStatePerDataset } from '../../../../../providers/media-upload-provider/media-upload-reducer';
import { DatasetMediaUploadActions } from '../../../../../providers/media-upload-provider/media-upload-reducer-actions';
import { ErrorListItem, UploadMedia } from '../../../../../providers/media-upload-provider/media-upload.interface';
import { useSelectedDataset } from '../use-selected-dataset/use-selected-dataset.hook';

export const useDatasetMediaUpload = () => {
    const { id } = useSelectedDataset();
    const {
        mediaUploadState: _mediaUploadState,
        onUploadMedia: _onUploadMedia,
        dispatch: _dispatch,
        abortMediaUploads,
        reset: _reset,
        retryUpload,
    } = useMediaUpload();

    const mediaUploadState = useMemo(
        () => _mediaUploadState[id] ?? getInitialStatePerDataset(),
        [_mediaUploadState, id]
    );

    const onUploadMedia = useCallback(
        (_uploadMedia: UploadMedia) => _onUploadMedia(id)(_uploadMedia),
        [_onUploadMedia, id]
    );

    const dispatch = useCallback(
        (action: DatasetMediaUploadActions) => _dispatch({ ...action, datasetId: id }),
        [_dispatch, id]
    );

    const abort = useMemo(() => abortMediaUploads(id), [abortMediaUploads, id]);

    const reset = useMemo(() => _reset(id), [_reset, id]);

    const retry = useCallback((errorItem: ErrorListItem) => retryUpload(id)(errorItem), [retryUpload, id]);

    return {
        mediaUploadState,
        onUploadMedia,
        dispatch,
        abort,
        reset,
        retry,
    };
};
