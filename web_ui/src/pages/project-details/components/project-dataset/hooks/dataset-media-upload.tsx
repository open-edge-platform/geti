// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
