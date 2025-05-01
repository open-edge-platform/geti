// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo, useRef } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { Loading } from '@shared/components/loading/loading.component';
import { MediaItemsList } from '@shared/components/media-items-list/media-items-list.component';
import { ViewModes } from '@shared/components/media-view-modes/utils';
import { NotFound } from '@shared/components/not-found/not-found.component';
import { useGroupedMediaItems } from '@shared/hooks/use-grouped-media-items.hook';
import { useSelectedMediaItemIndex } from '@shared/hooks/use-selected-media-item-index.hook';
import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';
import isEmpty from 'lodash/isEmpty';
import { VirtuosoGridHandle } from 'react-virtuoso';

import { MediaAdvancedFilterResponse, MediaItem, MediaItemResponse } from '../../../../../core/media/media.interface';
import { usePrevious } from '../../../../../hooks/use-previous/use-previous.hook';
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

export const DatasetList = ({
    viewMode,
    isReadOnly,
    mediaItemsQuery,
    selectMediaItem,
    hasTooltip = true,
    selectedMediaItem,
    isInActiveMode = false,
    isMediaFilterEmpty = false,
    previouslySelectedMediaItem,
    shouldShowAnnotationIndicator,
}: DatasetListProps): JSX.Element => {
    const ref = useRef<VirtuosoGridHandle | null>(null);

    const { hasNextPage, isPending: isMediaItemsLoading, isFetchingNextPage, fetchNextPage, data } = mediaItemsQuery;

    const mediaItems = useMemo(() => data?.pages?.flatMap(({ media }) => media) ?? [], [data?.pages]);
    const prevViewMode = usePrevious(viewMode);

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

    useEffect(() => {
        let timeoutId: ReturnType<typeof setTimeout> | null = null;
        const mediaItemChanged = previouslySelectedMediaItem?.identifier !== selectedMediaItem?.identifier;
        const viewModeChanged = prevViewMode !== viewMode;

        // We want to automatically scroll to the previously selected media.
        // But only if the media item or view mode is different.
        if ((mediaItemChanged || viewModeChanged) && ref.current) {
            timeoutId = setTimeout(() => {
                ref.current?.scrollToIndex({
                    index: mediaItemIndex,
                    behavior: 'smooth',
                    align: 'center',
                });
                // we don't want to scroll immediately
                // in case of changed view mode we have to scroll once view is rendered
            }, 500);
        }

        return () => {
            timeoutId && clearTimeout(timeoutId);
        };

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [viewMode, selectedMediaItem?.identifier, previouslySelectedMediaItem?.identifier, prevViewMode]);

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
                <Loading size={'M'} id={'dataset-main-loader-id'} />
            </Flex>
        );
    }

    return (
        <>
            <MediaItemsList
                id='annotator-dataset-list'
                ariaLabel={'Annotator dataset list'}
                ref={ref}
                viewMode={viewMode}
                totalCount={groupedMediaItems.length}
                endReached={loadNextMedia}
                itemContent={(index) => {
                    const mediaItem = groupedMediaItems[index];

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
