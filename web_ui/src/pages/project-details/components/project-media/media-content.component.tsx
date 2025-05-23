// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, useCallback, useMemo } from 'react';

import { paths } from '@geti/core';
import { Flex } from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { DatasetMediaUploadActions } from '../../../../providers/media-upload-provider/media-upload-reducer-actions';
import {
    MEDIA_CONTENT_BUCKET,
    MediaUploadPerDataset,
    UploadMedia,
} from '../../../../providers/media-upload-provider/media-upload.interface';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { MediaContentBucket } from './media-content-bucket.component';

interface MediaContentProps {
    mediaUploadState: MediaUploadPerDataset;
    dispatch: Dispatch<DatasetMediaUploadActions>;
    onUploadMedia: (uploadMedia: UploadMedia) => Promise<void>;
}

export const MediaContent = ({ mediaUploadState, dispatch, onUploadMedia }: MediaContentProps): JSX.Element => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();

    const { isUploadInProgress } = mediaUploadState;

    const uploadMediaMetadata = useMemo(() => ({ mediaUploadState, dispatch }), [mediaUploadState, dispatch]);

    const handleUploadMediaCallback = useCallback(
        (files: File[]): void => {
            onUploadMedia({ datasetIdentifier, files });
        },
        [datasetIdentifier, onUploadMedia]
    );
    const handleCameraSelected = useCallback(
        () => navigate(paths.project.dataset.camera(datasetIdentifier)),
        [navigate, datasetIdentifier]
    );

    const isMediaDropVisible = (isMediaFetching: boolean, hasMediaItems: boolean, isMediaFilterEmpty: boolean) => {
        if (isUploadInProgress && !hasMediaItems) {
            return true;
        }

        return !isMediaFetching && !hasMediaItems && isMediaFilterEmpty && !isUploadInProgress;
    };

    const isLoadingOverlayVisible = (isMediaFetching: boolean): boolean => {
        return isMediaFetching;
    };

    return (
        <Flex flex={1}>
            <MediaContentBucket
                mediaBucket={MEDIA_CONTENT_BUCKET.GENERIC}
                uploadMediaMetadata={uploadMediaMetadata}
                isMediaDropVisible={isMediaDropVisible}
                isLoadingOverlayVisible={isLoadingOverlayVisible}
                handleUploadMediaCallback={handleUploadMediaCallback}
                onCameraSelected={handleCameraSelected}
                showExportImportButton
            />
        </Flex>
    );
};
