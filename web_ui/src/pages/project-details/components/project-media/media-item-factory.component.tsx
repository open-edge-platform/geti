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

import { memo } from 'react';

import { MediaItem } from '../../../../core/media/media.interface';
import { useNavigateToAnnotatorRoute } from '../../../../core/services/use-navigate-to-annotator-route.hook';
import { ViewModes } from '../../../../shared/components/media-view-modes/utils';
import { isSelected } from '../../../annotator/components/sidebar/dataset/utils';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { getMediaId } from '../../../media/utils';
import { GridMediaItem } from './grid-media-item.component';
import { MediaItemDetails } from './media-item-details.component';

interface MediaItemFactoryProps {
    viewMode: ViewModes;
    mediaItem: MediaItem;
    isLargeSize: boolean;
    shouldShowAnnotationIndicator: boolean;
    mediaSelection: MediaItem[];
    toggleItemInMediaSelection: (mediaItem: MediaItem) => void;
}

export const MediaItemFactory = memo(
    ({
        viewMode,
        mediaItem,
        isLargeSize,
        shouldShowAnnotationIndicator,
        mediaSelection,
        toggleItemInMediaSelection,
    }: MediaItemFactoryProps): JSX.Element => {
        const datasetIdentifier = useDatasetIdentifier();
        const navigate = useNavigateToAnnotatorRoute(datasetIdentifier);

        const id = getMediaId(mediaItem);
        const isMediaItemSelected = mediaSelection.some((selectedMedia) => isSelected(selectedMedia, mediaItem));
        const isAtLeastOneMediaItemSelected = mediaSelection.length > 0;

        const toggleMediaSelection = () => {
            toggleItemInMediaSelection(mediaItem);
        };

        const handleDblClick = (): void => {
            navigate({ ...datasetIdentifier, mediaItem });
        };

        return viewMode === ViewModes.DETAILS ? (
            <MediaItemDetails
                id={id}
                mediaItem={mediaItem}
                isSelected={isMediaItemSelected}
                handleDblClick={handleDblClick}
                toggleMediaSelection={toggleMediaSelection}
                shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
            />
        ) : (
            <GridMediaItem
                id={id}
                isAtLeastOneMediaItemSelected={isAtLeastOneMediaItemSelected}
                mediaItem={mediaItem}
                isLargeSize={isLargeSize}
                isSelected={isMediaItemSelected}
                handleDblClick={handleDblClick}
                toggleMediaSelection={toggleMediaSelection}
                shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
            />
        );
    }
);
