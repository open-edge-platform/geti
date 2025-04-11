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

import { InfiniteData, QueryKey, useMutation, UseMutationResult, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { MediaAdvancedFilterResponse, MediaItem } from '../../../../core/media/media.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
import { getErrorMessage } from '../../../../core/services/utils';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { filterPageMedias } from '../../utils';

interface UseDeleteMediaMutation {
    deleteMedia: UseMutationResult<unknown, AxiosError, MediaItem[]>;
}

const getQueriesAndPreviousItems = (
    previousItems: [QueryKey, InfiniteData<MediaAdvancedFilterResponse> | undefined][]
) => {
    return previousItems.reduce<{
        queryKeys: QueryKey[];
        data: (InfiniteData<MediaAdvancedFilterResponse> | undefined)[];
    }>(
        (accumulator, current) => {
            accumulator.queryKeys.push(current[0]);
            accumulator.data.push(current[1]);

            return accumulator;
        },
        { queryKeys: [], data: [] }
    );
};

export const useDeleteMediaMutation = (): UseDeleteMediaMutation => {
    const queryClient = useQueryClient();
    const { addNotification } = useNotification();
    const { mediaService } = useApplicationServices();
    const datasetIdentifier = useDatasetIdentifier();
    const mediaQueryKeyPrefix = QUERY_KEYS.ADVANCED_MEDIA_ITEMS(datasetIdentifier, {}, {}).slice(0, 2);

    const deleteMedia = useMutation<
        unknown,
        AxiosError,
        MediaItem[],
        [QueryKey, InfiniteData<MediaAdvancedFilterResponse> | undefined][]
    >({
        mutationFn: (mediaItems) => {
            return Promise.all(mediaItems.map((mediaItem) => mediaService.deleteMedia(datasetIdentifier, mediaItem)));
        },

        onError: (error, _variables, previousItems) => {
            if (previousItems !== undefined) {
                const { queryKeys, data } = getQueriesAndPreviousItems(previousItems);
                queryClient.setQueriesData({ queryKey: queryKeys }, data);
            }

            addNotification({
                message: `Media cannot be deleted. ${getErrorMessage(error) ?? ''}`,
                type: NOTIFICATION_TYPE.ERROR,
            });
        },

        onMutate: (itemsDeleted) => {
            const previousItems = queryClient.getQueriesData<InfiniteData<MediaAdvancedFilterResponse>>({
                queryKey: mediaQueryKeyPrefix,
            });

            const deletedIdentifiers = itemsDeleted.map((item) => item.identifier);

            queryClient.setQueriesData<InfiniteData<MediaAdvancedFilterResponse>>(
                { queryKey: mediaQueryKeyPrefix },
                (currentData) => {
                    if (currentData === undefined) {
                        return undefined;
                    }

                    return filterPageMedias(currentData, deletedIdentifiers);
                }
            );

            return previousItems;
        },
        onSettled: async () => {
            await queryClient.invalidateQueries({ queryKey: mediaQueryKeyPrefix });
        },
    });

    return { deleteMedia };
};
