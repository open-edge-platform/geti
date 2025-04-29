// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { MediaItem } from '../../../../../core/media/media.interface';
import { ViewModes } from '../../../../../shared/components/media-view-modes/utils';
import { PressableElement } from '../../../../../shared/components/pressable-element/pressable-element.component';
import { DatasetItemGridMenu } from './dataset-item-grid-menu.component';
import { DatasetItemMenu } from './dataset-item-menu.component';
import { DatasetListItemDetails } from './dataset-list-item-details.component';
import { DatasetListItem } from './dataset-list-item.component';
import { isSelected } from './utils';

interface DatasetItemFactoryProps {
    isReadOnly: boolean;
    viewMode: ViewModes;
    mediaItem: MediaItem;
    selectedMediaItem: MediaItem | undefined;
    selectMediaItem: (mediaItem: MediaItem) => void;
    tooltip: JSX.Element | undefined;
    shouldShowAnnotationIndicator: boolean;
    shouldShowVideoIndicator?: boolean;
}

export const DatasetItemFactory = ({
    viewMode,
    mediaItem,
    selectedMediaItem,
    tooltip,
    isReadOnly,
    selectMediaItem,
    shouldShowAnnotationIndicator,
    shouldShowVideoIndicator = true,
}: DatasetItemFactoryProps): JSX.Element => {
    const isMediaSelected = isSelected(mediaItem, selectedMediaItem);

    return (
        <TooltipTrigger placement={'bottom'}>
            <PressableElement>
                {viewMode === ViewModes.DETAILS ? (
                    <DatasetListItemDetails
                        mediaItem={mediaItem}
                        isSelected={isMediaSelected}
                        selectMediaItem={() => !isMediaSelected && selectMediaItem(mediaItem)}
                        shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                        datasetItemMenu={
                            isReadOnly ? undefined : (
                                <DatasetItemMenu mediaItem={mediaItem} isSelected={isMediaSelected} />
                            )
                        }
                        shouldShowVideoIndicator={shouldShowVideoIndicator}
                    />
                ) : (
                    <DatasetListItem
                        mediaItem={mediaItem}
                        isSelected={isMediaSelected}
                        selectMediaItem={() => !isMediaSelected && selectMediaItem(mediaItem)}
                        shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                        datasetItemMenu={
                            isReadOnly ? undefined : (
                                <DatasetItemGridMenu mediaItem={mediaItem} isSelected={isMediaSelected} />
                            )
                        }
                        shouldShowVideoIndicator={shouldShowVideoIndicator}
                    />
                )}
            </PressableElement>
            <Tooltip>{tooltip}</Tooltip>
        </TooltipTrigger>
    );
};
