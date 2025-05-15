// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch } from 'react';

import { Query, useMutation, UseMutationResult, useQueryClient } from '@tanstack/react-query';
import { AxiosError, AxiosResponse, isCancel } from 'axios';
import { StatusCodes } from 'http-status-codes';
import { isArray, isEmpty } from 'lodash-es';

import { AdvancedFilterOptions, SearchOptionsRule } from '../../core/media/media-filter.interface';
import { UploadMediaMutationResponse } from '../../core/media/media.interface';
import { MediaService } from '../../core/media/services/media-service.interface';
import { DatasetIdentifier } from '../../core/projects/dataset.interface';
import QUERY_KEYS from '../../core/requests/query-keys';
import { getErrorMessage } from '../../core/services/utils';
import { useDebouncedCallback } from '../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { MediaItemDTO } from './../../core/media/dtos/media.interface';
import { DatasetMediaUploadActions, MediaUploadActionTypes } from './media-upload-reducer-actions';
import { ProgressListItem } from './media-upload.interface';

interface UseMediaUploadQueries {
    uploadMedia: UseMutationResult<
        AxiosResponse<MediaItemDTO>,
        AxiosError,
        UploadMediaMutationResponse & { abortController: AbortController }
    >;
}

const getMediaQueryFilter = (datasetIdentifier: DatasetIdentifier, labelIds: string[]) => {
    const queryKey = QUERY_KEYS.ADVANCED_MEDIA_ITEMS(datasetIdentifier, {}, { sortBy: '', sortDir: '' });

    return {
        // First find all queries related to fetching media, ignoring the filters and sorting options
        queryKey: queryKey.slice(0, -2),
        // Next find queries that are known not to exclude media with the given label ids
        predicate: (query: Query) => {
            if (query.queryKey[2] === 'active') {
                return false;
            }

            const conditions = query.queryKey[2] as AdvancedFilterOptions;

            const isLabelRule = (rule: SearchOptionsRule) => rule.field === 'LABEL_ID' && rule.operator === 'IN';

            if (isEmpty(labelIds)) {
                // If we don't have any label ids then any query that does not have filter rules,
                // or doesn't have a specific rule for a label, should be returned
                return !conditions.rules || !conditions.rules.some(isLabelRule);
            }

            return (
                !conditions.rules ||
                // If a query contains a label rule make sure it includes the given label
                conditions.rules.some((rule) => {
                    if (!isLabelRule(rule)) {
                        return false;
                    }

                    return (
                        isArray(rule.value) &&
                        rule.value.some((value) => {
                            return labelIds.includes(value);
                        })
                    );
                })
            );
        },
    };
};

/*
    The 'onSuccess' and 'onError', if set on the mutation itself, will run after EVERY request.
    This is important because we need to update the upload state after EVERY request.
*/
export const useMediaUploadMutations = ({
    mediaService,
    dispatch,
}: {
    mediaService: MediaService;
    dispatch: Dispatch<DatasetMediaUploadActions>;
}): UseMediaUploadQueries => {
    const queryClient = useQueryClient();

    const refreshMedia = useDebouncedCallback((datasetIdentifier: DatasetIdentifier, labelIds: string[] = []) => {
        return queryClient.invalidateQueries({ queryKey: getMediaQueryFilter(datasetIdentifier, labelIds).queryKey });
    }, 1000);

    const uploadMedia = useMutation({
        mutationFn: async ({
            datasetIdentifier,
            uploadId,
            media,
            abortController,
        }: UploadMediaMutationResponse & { abortController: AbortController }) => {
            return mediaService.uploadMedia({
                datasetIdentifier,
                uploadId,
                media,
                onProgress: (uploadProgressProps: ProgressListItem) => {
                    dispatch({
                        type: MediaUploadActionTypes.UPDATE_PROCESSING_ITEM,
                        payload: { uploadId, progress: uploadProgressProps },
                        datasetId: datasetIdentifier.datasetId,
                    });
                },
                abortController,
            });
        },

        onSuccess: ({ data }, variables) => {
            const { datasetIdentifier, uploadId, media } = variables;
            const labelIds = media.uploadInfo?.label_ids ?? [];

            if (!isEmpty(data)) {
                dispatch({
                    type: MediaUploadActionTypes.ADD_TO_SUCCESS_LIST,
                    payload: {
                        uploadId,
                        datasetIdentifier,
                        fileName: media.file.name,
                        fileType: media.file.type,
                        fileSize: media.file.size,
                        meta: media.meta,
                    },
                    datasetId: datasetIdentifier.datasetId,
                });
            }

            return refreshMedia(datasetIdentifier, labelIds);
        },

        onError: (error: AxiosError, variables) => {
            const { datasetIdentifier, uploadId, media } = variables;

            const { response } = error;
            const { datasetId } = datasetIdentifier;
            const errorMessage = getErrorMessage(error);

            if (isCancel(error)) {
                return;
            }

            if (response?.status === StatusCodes.INSUFFICIENT_STORAGE) {
                // cancel pending media upload
                dispatch({
                    datasetId,
                    type: MediaUploadActionTypes.CLEAR_WAITING_QUEUE,
                });

                // set insufficient storage to show a right message
                dispatch({
                    datasetId,
                    type: MediaUploadActionTypes.SET_INSUFFICIENT_STORAGE,
                    payload: true,
                });
            } else {
                dispatch({
                    type: MediaUploadActionTypes.ADD_TO_ERROR_LIST,
                    payload: {
                        uploadId,
                        datasetIdentifier,
                        meta: media.meta,
                        uploadInfo: media.uploadInfo,
                        file: media.file,
                        fileName: media.file.name,
                        fileType: media.file.type,
                        fileSize: media.file.size,
                        status: response?.status || 0,
                        statusText: response?.statusText || null,
                        errors: errorMessage ? [errorMessage] : [],
                    },
                    datasetId,
                });
            }

            // If the query fails, then we want to refetch all media items again because
            // we're doing optimistic updates and the uploaded media can be out of sync.
            const labelIds = media.uploadInfo?.label_ids ?? [];

            return refreshMedia(datasetIdentifier, labelIds);
        },
    });

    return { uploadMedia };
};
