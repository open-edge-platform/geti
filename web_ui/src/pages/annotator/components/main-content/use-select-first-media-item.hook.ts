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

import { useEffect } from 'react';

import isEmpty from 'lodash/isEmpty';

import { MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { useDataset } from '../../providers/dataset-provider/dataset-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useMediaIdentifierFromRoute } from '../../providers/selected-media-item-provider/utils';

export const getMediaItemToSelect = (mediaItems: MediaItem[]): MediaItem => {
    // Help the user by selecting an item that's not been annotated
    const firstUnannotatedMediaItem = mediaItems.find((media) => {
        return media.status === MEDIA_ANNOTATION_STATUS.NONE;
    });

    return firstUnannotatedMediaItem !== undefined ? firstUnannotatedMediaItem : mediaItems[0];
};

export const useSelectFirstMediaItem = (): void => {
    const mediaIdentifier = useMediaIdentifierFromRoute();

    const { setSelectedMediaItem } = useSelectedMediaItem();
    const { mediaItemsQuery } = useDataset();
    const { isFetching, data } = mediaItemsQuery;

    useEffect(() => {
        if (data !== undefined && !isFetching) {
            const mediaItems = data.pages.flatMap(({ media }) => media);

            if (isEmpty(mediaItems)) {
                return;
            }

            if (mediaIdentifier !== undefined) {
                return;
            }

            setSelectedMediaItem(getMediaItemToSelect(mediaItems));
        }
    }, [data, setSelectedMediaItem, isFetching, mediaIdentifier]);
};
