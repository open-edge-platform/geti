// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';
import isNil from 'lodash/isNil';

import { MediaAdvancedFilterResponse, MediaItem, MediaItemResponse } from '../../../../../core/media/media.interface';
import { TestMediaAdvancedFilter, TestMediaItem } from '../../../../../core/tests/test-media.interface';
import { useGroupedMediaItems } from '../../../../hooks/use-grouped-media-items.hook';
import { ControlType, ImagePreviewControl } from './image-preview-control/image-preview-control.component';
import { getSelectedItemIndex } from './utils';

interface ImagePreviewNavigationControlsProps<T> {
    mediaItemsQuery: UseInfiniteQueryResult<
        InfiniteData<MediaItemResponse | MediaAdvancedFilterResponse | TestMediaAdvancedFilter>
    >;
    selectedMediaItem: T;
    changeSelectedItem: (item: T) => void;
    showFramesSeparately?: boolean;
}

export const ImagePreviewNavigationControls = <T extends MediaItem | TestMediaItem>({
    mediaItemsQuery,
    selectedMediaItem,
    changeSelectedItem,
    showFramesSeparately = false,
}: ImagePreviewNavigationControlsProps<T>): JSX.Element => {
    const allMediaItems: (MediaItem | TestMediaItem)[] = useMemo(() => {
        const { isSuccess, data } = mediaItemsQuery;

        if (isSuccess && !isNil(data)) {
            return data.pages.flatMap((item) => item.media as T[]);
        }

        return [];
    }, [mediaItemsQuery]);

    const groupedMediaItems = useGroupedMediaItems(allMediaItems);

    const mediaItems = showFramesSeparately ? allMediaItems : groupedMediaItems;

    const isNextDisabled = useMemo((): boolean => {
        const index = getSelectedItemIndex(selectedMediaItem, mediaItems, showFramesSeparately);

        return index >= mediaItems.length - 1;
    }, [selectedMediaItem, mediaItems, showFramesSeparately]);

    const gotoNext = () => {
        const index = getSelectedItemIndex(selectedMediaItem, mediaItems, showFramesSeparately);

        if (index !== undefined && index < mediaItems.length - 1) {
            changeSelectedItem(mediaItems[index + 1] as T);
        }
    };

    const isPreviousDisabled = useMemo((): boolean => {
        const index = getSelectedItemIndex(selectedMediaItem, mediaItems, showFramesSeparately);

        return index <= 0;
    }, [selectedMediaItem, mediaItems, showFramesSeparately]);

    const gotoPrevious = () => {
        const index = getSelectedItemIndex(selectedMediaItem, mediaItems, showFramesSeparately);

        if (index !== undefined && index > 0) {
            changeSelectedItem(mediaItems[index - 1] as T);
        }
    };

    return (
        <>
            {!isPreviousDisabled && <ImagePreviewControl type={ControlType.PREVIOUS} onClick={gotoPrevious} />}
            {!isNextDisabled && <ImagePreviewControl type={ControlType.NEXT} onClick={gotoNext} />}
        </>
    );
};
