// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Flex, Loading } from '@geti/ui';
import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { MediaAdvancedFilterResponse, MediaItem, MediaItemResponse } from '../../../../../core/media/media.interface';
import { MediaItemsList } from '../../../../../shared/components/media-items-list/media-items-list.component';
import { ViewModes } from '../../../../../shared/components/media-view-modes/utils';
import { NotFound } from '../../../../../shared/components/not-found/not-found.component';
import { useGroupedMediaItems } from '../../../../../shared/hooks/use-grouped-media-items.hook';
import { useSelectedMediaItemIndex } from '../../../../../shared/hooks/use-selected-media-item-index.hook';
import { getMediaId } from '../../../../media/utils';
import { MediaItemTooltipMessage } from '../../../../project-details/components/project-media/media-item-tooltip-message/media-item-tooltip-message';
import { getMediaItemTooltipProps } from '../../../../project-details/components/project-media/media-item-tooltip-message/utils';
import { DatasetItemFactory } from './dataset-item-factory.component';
import { EmptyDataSet } from './empty-dataset.component';

import classes from './dataset-accordion.module.scss';

interface DatasetListProps {
    selectedMediaItem?: MediaItem;
    previouslySelectedMediaItem?: MediaItem;
    selectMediaItem: (mediaItem: MediaItem) => void;
    mediaItemsQuery: UseInfiniteQueryResult<InfiniteData<MediaItemResponse | MediaAdvancedFilterResponse>>;
    viewMode: ViewModes;
    isInActiveMode?: boolean;
    isMediaFilterEmpty?: boolean;
    getItemTooltip?: (item: MediaItem) => JSX.Element;
    isReadOnly: boolean;
    shouldShowAnnotationIndicator: boolean;
    hasTooltip?: boolean;
}

const viewModeSettings = {
    [ViewModes.SMALL]: { minItemSize: 70, gap: 4, maxColumns: 11 },
    [ViewModes.MEDIUM]: { minItemSize: 100, gap: 4, maxColumns: 8 },
    [ViewModes.LARGE]: { minItemSize: 120, gap: 4, maxColumns: 4 },
    [ViewModes.DETAILS]: { size: 85, gap: 0 },
};

export const DatasetList = ({
    viewMode,
    isReadOnly,
    mediaItemsQuery,
    selectMediaItem,
    hasTooltip = true,
    selectedMediaItem,
    isInActiveMode = false,
    isMediaFilterEmpty = false,
    shouldShowAnnotationIndicator,
}: DatasetListProps): JSX.Element => {
    const { hasNextPage, isPending: isMediaItemsLoading, isFetchingNextPage, fetchNextPage, data } = mediaItemsQuery;

    const mediaItems = useMemo(() => data?.pages?.flatMap(({ media }) => media) ?? [], [data?.pages]);

    const loadNextMedia = async () => {
        if (isInActiveMode) {
            return;
        }

        if (!isFetchingNextPage && hasNextPage) {
            await fetchNextPage();
        }
    };

    const groupedMediaItems = useGroupedMediaItems(mediaItems);
    const mediaItemIndex = useSelectedMediaItemIndex(mediaItems, selectedMediaItem, isInActiveMode);

    const allPagesAreEmpty = data?.pages.every((page) => isEmpty(page.media));

    const shouldShowNotFound = allPagesAreEmpty && !isMediaItemsLoading && !isMediaFilterEmpty && !isInActiveMode;

    if (shouldShowNotFound) {
        return <NotFound />;
    }

    const shouldShowEmptyDataset = allPagesAreEmpty && !isMediaItemsLoading;

    if (shouldShowEmptyDataset) {
        return <EmptyDataSet isActiveMode={isInActiveMode} />;
    }

    if (isMediaItemsLoading) {
        return (
            <Flex position={'relative'} justifyContent='center' alignItems='center' height={'100%'}>
                <Loading size={'M'} />
            </Flex>
        );
    }

    return (
        <>
            <MediaItemsList
                id='annotator-dataset-list'
                ariaLabel={'Annotator dataset list'}
                viewMode={viewMode}
                idFormatter={getMediaId}
                endReached={loadNextMedia}
                getTextValue={(item) => item.name}
                mediaItems={groupedMediaItems}
                viewModeSettings={viewModeSettings}
                scrollToIndex={mediaItemIndex}
                itemContent={(mediaItem) => {
                    return (
                        <DatasetItemFactory
                            viewMode={viewMode}
                            mediaItem={mediaItem}
                            isReadOnly={isReadOnly}
                            selectMediaItem={selectMediaItem}
                            selectedMediaItem={selectedMediaItem}
                            shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                            tooltip={
                                hasTooltip && viewMode !== ViewModes.DETAILS ? (
                                    <MediaItemTooltipMessage {...getMediaItemTooltipProps(mediaItem)} />
                                ) : undefined
                            }
                            shouldShowVideoIndicator={!isInActiveMode}
                        />
                    );
                }}
            />
            {isFetchingNextPage && (
                <Flex justifyContent='center' alignItems='center' UNSAFE_className={classes.fetchingWrapper}>
                    <Loading size={'M'} />
                </Flex>
            )}
        </>
    );
};
