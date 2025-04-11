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

import { Dispatch, useCallback, useMemo } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { useNavigate } from 'react-router-dom';

import { paths } from '../../../../core/services/routes';
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
