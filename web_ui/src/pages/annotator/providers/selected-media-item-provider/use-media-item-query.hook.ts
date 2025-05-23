// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { isEqual } from 'lodash-es';

import { MediaIdentifier, MediaItem } from '../../../../core/media/media.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';

export const useMediaItemQuery = (
    datasetIdentifier: DatasetIdentifier,
    mediaItemId: MediaIdentifier | undefined,
    options: Pick<UseQueryOptions<MediaItem>, 'enabled' | 'placeholderData'>,
    onSuccess?: (data: MediaItem) => void
) => {
    const { mediaService } = useApplicationServices();
    const { addNotification } = useNotification();
    const handleSuccessRef = useRef(onSuccess);

    const query = useQuery<MediaItem>({
        queryKey: QUERY_KEYS.MEDIA_ITEM(datasetIdentifier, mediaItemId),
        queryFn: async () => {
            if (mediaItemId === undefined) {
                throw new Error('Could not retrieve media item');
            }

            const media = await mediaService.getMediaItem(datasetIdentifier, mediaItemId);

            if (media === undefined) {
                throw new Error('Could not retrieve media item');
            }

            if (!isEqual(media.identifier, mediaItemId)) {
                throw new Error('Received a media item with a different identifier');
            }

            return media;
        },
        enabled: mediaItemId !== undefined,
        ...options,
    });

    useEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    useEffect(() => {
        if (!options.enabled || !query.isSuccess || handleSuccessRef.current === undefined) {
            return;
        }

        handleSuccessRef.current(query.data);
    }, [options.enabled, query.isSuccess, query.data]);

    useEffect(() => {
        if (!options.enabled || !query.isError) {
            return;
        }

        addNotification({ message: 'Could not retrieve media item', type: NOTIFICATION_TYPE.ERROR });
    }, [options.enabled, query.isError, addNotification]);

    return query;
};
