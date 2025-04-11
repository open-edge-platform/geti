// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { Divider, Flex, Text } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import { useMediaQuery } from '@react-spectrum/utils';
import { useParams } from 'react-router-dom';

import { AdvancedFilterOptions, SearchRuleField } from '../../../../core/media/media-filter.interface';
import { useTests } from '../../../../core/tests/hooks/use-tests.hook';
import { TestMediaItem } from '../../../../core/tests/test-media.interface';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { useViewMode } from '../../../../hooks/use-view-mode/use-view-mode.hook';
import { MediaViewModes } from '../../../../shared/components/media-view-modes/media-view-modes.component';
import { ViewModes } from '../../../../shared/components/media-view-modes/utils';
import {
    SortByAttribute,
    SortDirection,
} from '../../../../shared/components/sort-by-attribute/sort-by-attribute.component';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { getMatchedMediaCounts } from '../../utils';
import { MediaItemsBucketTitle, MediaItemsBucketType } from './media-items-bucket.interface';
import { TestMediaItemsList } from './test-media-items-list.component';

import classes from './project-test.module.scss';

interface MediaItemsBucketProps {
    type: MediaItemsBucketType;
    title: MediaItemsBucketTitle;
    mediaFilterOptions: AdvancedFilterOptions;
    setSelectedTestItem: (testMediaItem: TestMediaItem, sortDir: SortDirection) => void;
    selectedMediaItem?: TestMediaItem;
    selectedLabelId?: string;
}

export const MediaItemsBucket = ({
    type,
    title,
    selectedLabelId,
    selectedMediaItem,
    mediaFilterOptions,
    setSelectedTestItem,
}: MediaItemsBucketProps): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { testId } = useParams<{ testId: string }>();
    const [viewMode, setViewMode] = useViewMode(type, ViewModes.SMALL);

    const isNotLargeSize = !useMediaQuery(isLargeSizeQuery);

    const isBelowThresholdBucket = type === MediaItemsBucketType.BELOW_THRESHOLD;
    const [sortDirection, setSortDirection] = useState<SortDirection>(SortDirection.ASC);

    const { useMediaItemsOfTestQuery } = useTests();
    const testMediaItemsQuery = useMediaItemsOfTestQuery(projectIdentifier, testId ?? '', mediaFilterOptions, {
        sortBy: SearchRuleField.Score,
        sortDir: sortDirection,
    });
    const { isFetchingNextPage, hasNextPage, fetchNextPage, data: mediaData } = testMediaItemsQuery;

    const { totalMatchedVideos = 0, totalMatchedImages = 0, totalMatchedVideoFrames = 0 } = mediaData?.pages[0] ?? {};

    const loadNextMedia = async (): Promise<void> => {
        if (!isFetchingNextPage && hasNextPage) {
            await fetchNextPage();
        }
    };

    const bucketId = idMatchingFormat(type.toLowerCase());
    const bucketContainerId = `${bucketId}-bucket-container-id`;
    const sortIconId = `${bucketId}-sort-icon-${sortDirection}-id`;
    const mediaCountsId = `${bucketId}-media-counts-id`;

    return (
        <Flex
            direction={'column'}
            flex={1}
            minHeight={'size-2400'}
            gap={'size-200'}
            UNSAFE_className={`${classes.mediaBucketContainer} ${
                isBelowThresholdBucket ? classes.mediaBucketBelow : classes.mediaBucketAbove
            }`}
            data-testid={bucketContainerId}
            id={bucketContainerId}
        >
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Flex alignItems={'center'}>
                    <Heading data-testid={'bucket-title-id'} margin={0}>
                        {title}
                    </Heading>
                    {isNotLargeSize && <Divider size={'S'} orientation={'vertical'} marginX={'size-100'} />}
                </Flex>
                <Text UNSAFE_className={classes.mediaItemsCount} id={mediaCountsId}>
                    {getMatchedMediaCounts(totalMatchedImages, totalMatchedVideoFrames, totalMatchedVideos)}
                </Text>
            </Flex>
            <Flex direction={'column'} flex={1} minHeight={0} UNSAFE_className={classes.mediaItemsBucket}>
                <Flex alignItems={'center'} justifyContent={'space-between'} marginBottom={'size-200'}>
                    <SortByAttribute
                        label='Model score'
                        sortDirection={sortDirection}
                        setSortDirection={setSortDirection}
                        sortIconId={sortIconId}
                        attributeName={SearchRuleField.Score}
                    />
                    <MediaViewModes viewMode={viewMode} setViewMode={setViewMode} />
                </Flex>

                <TestMediaItemsList
                    viewMode={viewMode}
                    loadNextMedia={loadNextMedia}
                    selectedLabelId={selectedLabelId}
                    mediaItemsQuery={testMediaItemsQuery}
                    shouldShowAnnotationIndicator={false}
                    selectMediaItem={(selectedItem) => setSelectedTestItem(selectedItem, sortDirection)}
                    selectedMediaItem={selectedMediaItem?.media}
                />
            </Flex>
        </Flex>
    );
};
