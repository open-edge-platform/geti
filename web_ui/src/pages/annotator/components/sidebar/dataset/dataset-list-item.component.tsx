// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { View } from '@adobe/react-spectrum';

import { MediaItem } from '../../../../../core/media/media.interface';
import { MediaItemView } from '../../../../../shared/components/media-item-view/media-item-view.component';
import { getMediaId } from '../../../../media/utils';

import classes from './dataset-accordion.module.scss';

const SELECTED_PROPS = Object.freeze({ borderColor: 'informative', borderWidth: 'thick' });

interface DatasetListItemProps {
    mediaItem: MediaItem;
    isSelected: boolean;
    selectMediaItem: () => void;
    datasetItemMenu?: ReactNode;
    shouldShowAnnotationIndicator: boolean;
    shouldShowVideoIndicator?: boolean;
}

export const DatasetListItem = ({
    mediaItem,
    isSelected,
    selectMediaItem,
    datasetItemMenu,
    shouldShowAnnotationIndicator,
    shouldShowVideoIndicator = true,
}: DatasetListItemProps): JSX.Element => {
    const selectedProps = isSelected ? SELECTED_PROPS : {};
    const id = getMediaId(mediaItem);

    return (
        <View position='relative' height='100%' width='100%' {...selectedProps}>
            <div
                id={id}
                data-testid={id}
                onClick={selectMediaItem}
                className={classes.datasetItem}
                aria-label={`Dataset item ${id}`}
            >
                <MediaItemView
                    mediaItem={mediaItem}
                    itemMenu={datasetItemMenu}
                    shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                    shouldShowVideoIndicator={shouldShowVideoIndicator}
                />
            </div>
        </View>
    );
};
