// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { MediaItem } from '../../../../core/media/media.interface';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { getImageData } from '../../../../shared/canvas-utils';
import { loadImage } from '../../../../shared/utils';

export const useLoadImageQuery = (mediaItem: MediaItem | undefined): UseQueryResult<ImageData, AxiosError> => {
    return useQuery({
        queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.IMAGE(mediaItem?.identifier),
        queryFn: async () => {
            if (mediaItem === undefined) {
                throw new Error("Can't fetch undefined media item");
            }

            const image = await loadImage(mediaItem.src);

            return getImageData(image);
        },
        enabled: mediaItem !== undefined,
        // The image of a media item never changes so we don't want to refetch stale data
        staleTime: Infinity,
        retry: 0,
    });
};
