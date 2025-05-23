// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { getErrorMessage } from '@geti/core/src/services/utils';
import { InfiniteData, QueryKey, useMutation, UseMutationResult, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { MediaAdvancedFilterResponse, MediaItem } from '../../../../core/media/media.interface';
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
