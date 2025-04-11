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
