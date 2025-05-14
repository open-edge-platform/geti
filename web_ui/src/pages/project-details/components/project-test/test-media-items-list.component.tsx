// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo, useRef } from 'react';

import { Flex, IllustratedMessage, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { InfiniteData, UseInfiniteQueryResult } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';
import { VirtuosoGridHandle } from 'react-virtuoso';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { TestImageMediaItem } from '../../../../core/tests/test-image.interface';
import { TestMediaAdvancedFilter, TestMediaItem } from '../../../../core/tests/test-media.interface';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { MediaItemsList } from '../../../../shared/components/media-items-list/media-items-list.component';
import { ViewModes } from '../../../../shared/components/media-view-modes/utils';
import { NotFound } from '../../../../shared/components/not-found/not-found.component';
import { PressableElement } from '../../../../shared/components/pressable-element/pressable-element.component';
import { useSelectedMediaItemIndex } from '../../../../shared/hooks/use-selected-media-item-index.hook';
import { isSelected } from '../../../annotator/components/sidebar/dataset/utils';
import { MediaItemTooltipMessage } from '../project-media/media-item-tooltip-message/media-item-tooltip-message';
import { getMediaItemTooltipProps } from '../project-media/media-item-tooltip-message/utils';
import { TestMediaItemCard } from './test-media-item-card.component';
import { TestMediaItemDetailsCard } from './test-media-item-details-card.component';
import { isEqualLabelId } from './utils';

interface TestMediaItemsListProps {
    viewMode: ViewModes;
    loadNextMedia: () => Promise<void>;
    mediaItemsQuery: UseInfiniteQueryResult<InfiniteData<TestMediaAdvancedFilter>>;
    selectMediaItem: (mediaItem: TestMediaItem) => void;
    shouldShowAnnotationIndicator: boolean;
    selectedMediaItem?: MediaItem;
    selectedLabelId?: string;
}

const viewModeSettings = {
    [ViewModes.SMALL]: { minItemSize: 70, gap: 4, maxColumns: 6 },
    [ViewModes.MEDIUM]: { minItemSize: 90, gap: 4, maxColumns: 4 },
    [ViewModes.LARGE]: { minItemSize: 100, gap: 4, maxColumns: 2 },
    [ViewModes.DETAILS]: { size: 85, gap: 0 },
};

const getTestMediaItemId = (item: TestMediaItem) => {
    const annotationId = 'testResult' in item ? item.testResult.annotationId : '';

    if (item.type === MEDIA_TYPE.IMAGE) {
        return `${item.media.identifier.imageId}-${annotationId}`;
    }

    return `${item.media.identifier.videoId}-${annotationId}`;
};

export const TestMediaItemsList = ({
    viewMode,
    selectedLabelId,
    mediaItemsQuery,
    selectedMediaItem,
    shouldShowAnnotationIndicator,
    loadNextMedia,
    selectMediaItem,
}: TestMediaItemsListProps): JSX.Element => {
    const ref = useRef<VirtuosoGridHandle | null>(null);
    const { isLoading: isMediaItemsLoading, isFetchingNextPage, data } = mediaItemsQuery;
    const mediaItems = useMemo(() => data?.pages?.flatMap(({ media }) => media) ?? [], [data?.pages]);

    const allPagesAreEmpty = data?.pages?.every((page) => isEmpty(page.media));

    const hasMediaItems = !allPagesAreEmpty && !isMediaItemsLoading;

    const mediaItemIndex = useSelectedMediaItemIndex(mediaItems, selectedMediaItem, false, true);

    useEffect(() => {
        let timeoutId: ReturnType<typeof setTimeout> | null = null;

        if (ref.current && selectedMediaItem !== undefined) {
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
    }, [selectedMediaItem]);

    if (isMediaItemsLoading) {
        return (
            <Flex position={'relative'} alignItems={'center'} justifyContent={'center'} height={'100%'}>
                <Loading size={'M'} />
            </Flex>
        );
    }

    return (
        <Flex
            direction='column'
            flex={1}
            gap='size-100'
            position='relative'
            UNSAFE_style={{ overflow: 'hidden' }}
            height='100%'
        >
            <IllustratedMessage isHidden={hasMediaItems}>
                <NotFound />
            </IllustratedMessage>

            {hasMediaItems && (
                <Flex direction={'column'} position={'relative'} height={'100%'} width={'100%'}>
                    <View flex={1}>
                        <MediaItemsList
                            viewMode={viewMode}
                            endReached={loadNextMedia}
                            mediaItems={mediaItems}
                            viewModeSettings={viewModeSettings}
                            idFormatter={getTestMediaItemId}
                            getTextValue={(item) => item.media.name}
                            itemContent={(mediaItem) => {
                                const mediaImageItem = mediaItem as unknown as TestImageMediaItem;
                                const handleSelectMediaItem = () => selectMediaItem(mediaItem);

                                const tooltipProps = getMediaItemTooltipProps(mediaItem.media);
                                const isMediaSelected =
                                    selectedMediaItem && isSelected(mediaItem.media, selectedMediaItem, true);

                                const testScores = mediaImageItem?.testResult?.scores ?? [];
                                const labelScore = testScores.find(
                                    isEqualLabelId(selectedLabelId === undefined ? 'null' : selectedLabelId)
                                );

                                return (
                                    <TooltipTrigger placement={'bottom'}>
                                        <PressableElement height={'100%'}>
                                            {viewMode === ViewModes.DETAILS ? (
                                                <TestMediaItemDetailsCard
                                                    mediaItem={mediaItem}
                                                    labelScore={labelScore}
                                                    selectMediaItem={handleSelectMediaItem}
                                                    isSelected={isMediaSelected}
                                                    shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                                                />
                                            ) : (
                                                <TestMediaItemCard
                                                    labelScore={labelScore}
                                                    mediaItem={mediaItem}
                                                    selectMediaItem={handleSelectMediaItem}
                                                    isSelected={isMediaSelected}
                                                    shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                                                />
                                            )}
                                        </PressableElement>
                                        <Tooltip>
                                            <MediaItemTooltipMessage {...tooltipProps} />
                                        </Tooltip>
                                    </TooltipTrigger>
                                );
                            }}
                        />
                    </View>
                    {isFetchingNextPage && (
                        <Flex position={'relative'} height={'size-675'}>
                            <Loading size={'M'} />
                        </Flex>
                    )}
                </Flex>
            )}
        </Flex>
    );
};
