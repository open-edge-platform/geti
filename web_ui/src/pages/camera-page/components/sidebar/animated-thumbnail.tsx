// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue, View, type DimensionValue } from '@geti/ui';
import { useOverlayTriggerState } from 'react-stately';

import { MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import { AnnotationStateIndicator } from '../../../../shared/components/annotation-indicator/annotation-state-indicator.component';
import { isNonEmptyArray } from '../../../../shared/utils';
import { DeleteItemButton } from '../delete-item-button.component';
import { ImageVideoFactory } from '../image-video-factory.component';

import classes from './sidebar.module.scss';

interface AnimatedThumbnailProps {
    id: string;
    url: string;
    labelIds: string[];
    size: DimensionValue;
    isVideo: boolean;
    hasDeleteButton?: boolean;
    onDeleteItem: (id: string) => void;
}

export const AnimatedThumbnail = ({
    id,
    url,
    size,
    isVideo,
    labelIds,
    hasDeleteButton = true,
    onDeleteItem,
}: AnimatedThumbnailProps) => {
    const alertDialogState = useOverlayTriggerState({});
    const isLabeled = isNonEmptyArray(labelIds);

    return (
        <View width={size} height={size} UNSAFE_className={classes.animatedThumbnailContainer}>
            <ImageVideoFactory
                src={url}
                aria-label={`media item ${id}`}
                alt={`media item ${id}`}
                isVideoFile={isVideo}
                style={{ objectFit: 'cover', width: dimensionValue(size), height: dimensionValue(size) }}
            />

            {hasDeleteButton && (
                <DeleteItemButton
                    id={id}
                    top={'size-50'}
                    right={'size-50'}
                    position={'absolute'}
                    onDeleteItem={onDeleteItem}
                    alertDialogState={alertDialogState}
                    UNSAFE_className={[classes.deleteContainer, alertDialogState.isOpen ? classes.visible : ''].join(
                        ' '
                    )}
                />
            )}

            <AnnotationStateIndicator
                id={`${id}-status`}
                state={isLabeled ? MEDIA_ANNOTATION_STATUS.ANNOTATED : MEDIA_ANNOTATION_STATUS.NONE}
            />
        </View>
    );
};
