// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, useCallback, useRef } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';

import { ConcurrentItemProcessor } from '../../shared/concurrent-item-processor/concurrent-item-processor';
import { DatasetMediaUploadActions, MediaUploadActionTypes } from './media-upload-reducer-actions';
import { QueuedListItem, ValidationFailReason } from './media-upload.interface';
import { validateMedia } from './media-upload.validator';
import { useMediaUploadMutations } from './use-media-upload-mutations';
import { getUploadsToBeRunConcurrently } from './utils';

export const useUploadQueueRef = (
    dispatch: Dispatch<DatasetMediaUploadActions>,
    abortControllers: Map<string, AbortController>
) => {
    const { mediaService } = useApplicationServices();
    const { uploadMedia: uploadMediaMutation } = useMediaUploadMutations({ mediaService, dispatch });

    const pushMedia = useCallback(
        async (uploadId: string, media: QueuedListItem) => {
            const datasetId = media.datasetIdentifier.datasetId;
            let abortController = abortControllers.get(datasetId);
            if (!abortController) {
                abortController = new AbortController();
                abortControllers.set(datasetId, abortController);
            }

            return uploadMediaMutation.mutateAsync({
                datasetIdentifier: media.datasetIdentifier,
                uploadId,
                media,
                abortController,
            });
        },
        [abortControllers, uploadMediaMutation]
    );

    const validateMediaFile = useCallback(
        async ({ media, uploadId }: { media: QueuedListItem; uploadId: string }): Promise<void> => {
            const { datasetIdentifier, file } = media;
            const { datasetId } = datasetIdentifier;

            await validateMedia(file).catch((reason: ValidationFailReason) => {
                dispatch({
                    type: MediaUploadActionTypes.ADD_TO_ERROR_LIST,
                    payload: {
                        uploadId,
                        datasetIdentifier,
                        meta: media.meta,
                        uploadInfo: media.uploadInfo,
                        statusText: null,
                        file: reason.file,
                        fileName: reason.file.name,
                        fileType: reason.file.type,
                        fileSize: reason.file.size,
                        status: reason.status,
                        errors: reason.errors,
                    },
                    datasetId,
                });

                return Promise.reject(`File "${reason.file.name}" has an invalid format type: "${reason.file.type}"`);
            });
        },
        [dispatch]
    );

    const processMedia = useCallback(
        async (media: QueuedListItem) => {
            const { datasetIdentifier, file, meta } = media;
            const { datasetId } = datasetIdentifier;
            const uploadId = media.uploadId;

            dispatch({
                type: MediaUploadActionTypes.UPDATE_PROCESSING_ITEM,
                payload: {
                    uploadId,
                    progress: {
                        uploadId,
                        datasetIdentifier,
                        file,
                        fileName: file.name,
                        fileType: file.type,
                        fileSize: file.size,
                        progress: 0,
                        meta,
                    },
                },
                datasetId,
            });

            try {
                await validateMediaFile({ media, uploadId });

                return pushMedia(uploadId, media);
            } catch (error) {
                console.error(error);
            }
        },
        [dispatch, pushMedia, validateMediaFile]
    );

    const uploadQueue = useRef(
        new ConcurrentItemProcessor(async (item: QueuedListItem) => {
            return processMedia(item);
        }, getUploadsToBeRunConcurrently)
    );

    return uploadQueue;
};
