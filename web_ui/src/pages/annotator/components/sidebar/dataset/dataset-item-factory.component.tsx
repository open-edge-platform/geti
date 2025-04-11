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

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { MediaItem } from '../../../../../core/media/media.interface';
import { ActionElement } from '../../../../../shared/components/action-element/action-element.component';
import { ViewModes } from '../../../../../shared/components/media-view-modes/utils';
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
            <ActionElement>
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
            </ActionElement>
            <Tooltip>{tooltip}</Tooltip>
        </TooltipTrigger>
    );
};
