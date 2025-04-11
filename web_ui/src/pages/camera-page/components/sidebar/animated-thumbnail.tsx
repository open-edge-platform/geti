// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DimensionValue } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import { AnimatePresence, motion } from 'framer-motion';
import { useOverlayTriggerState } from 'react-stately';

import { MEDIA_ANNOTATION_STATUS } from '../../../../core/media/base.interface';
import { ANIMATION_PARAMETERS } from '../../../../shared/animation-parameters/animation-parameters';
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
