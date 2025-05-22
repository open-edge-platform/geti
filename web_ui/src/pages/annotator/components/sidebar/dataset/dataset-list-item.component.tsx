// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { View } from '@geti/ui';

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
