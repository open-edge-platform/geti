// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { memo } from 'react';

import { useNavigateToAnnotatorRoute } from '@geti/core/src/services/use-navigate-to-annotator-route.hook';

import { MediaItem } from '../../../../core/media/media.interface';
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
        const navigate = useNavigateToAnnotatorRoute();

        const id = getMediaId(mediaItem);
        const isMediaItemSelected = mediaSelection.some((selectedMedia) => isSelected(selectedMedia, mediaItem));
        const isAtLeastOneMediaItemSelected = mediaSelection.length > 0;

        const toggleMediaSelection = () => {
            toggleItemInMediaSelection(mediaItem);
        };

        const handleDblClick = (): void => {
            navigate({ datasetIdentifier, mediaItem });
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
