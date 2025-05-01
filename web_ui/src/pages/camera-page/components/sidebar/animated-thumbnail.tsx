// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DimensionValue } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import { ANIMATION_PARAMETERS } from '@shared/animation-parameters/animation-parameters';
import { AnnotationStateIndicator } from '@shared/components/annotation-indicator/annotation-state-indicator.component';
import { isNonEmptyArray } from '@shared/utils';
import { AnimatePresence, motion } from 'framer-motion';
import { useOverlayTriggerState } from 'react-stately';

import { MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
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
        <AnimatePresence>
            <motion.div
                initial={'hidden'}
                animate={'visible'}
                className={classes.animatedThumbnailContainer}
                variants={ANIMATION_PARAMETERS.ANIMATE_ELEMENT_WITH_JUMP}
                style={{ width: dimensionValue(size), height: dimensionValue(size) }}
            >
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
                        UNSAFE_className={[
                            classes.deleteContainer,
                            alertDialogState.isOpen ? classes.visible : '',
                        ].join(' ')}
                    />
                )}

                <AnnotationStateIndicator
                    id={`${id}-status`}
                    state={isLabeled ? MEDIA_ANNOTATION_STATUS.ANNOTATED : MEDIA_ANNOTATION_STATUS.NONE}
                />
            </motion.div>
        </AnimatePresence>
    );
};
