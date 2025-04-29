// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
