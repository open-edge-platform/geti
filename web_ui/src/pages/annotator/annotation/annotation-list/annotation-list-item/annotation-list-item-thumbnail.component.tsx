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

import { memo, useEffect, useRef } from 'react';

import { Flex } from '@react-spectrum/layout';

import { Shape } from '../../../../../core/annotations/shapes.interface';
import { MEDIA_ANNOTATION_STATUS } from '../../../../../core/media/base.interface';
import { AnnotationStateIndicator } from '../../../../../shared/components/annotation-indicator/annotation-state-indicator.component';
import { cropCanvasBasedOnShape } from '../utils';

import classes from './annotation-list-thumbnail.module.scss';

interface AnnotationListItemThumbnailProps {
    annotationShape: Shape;
    annotationId: string;
    isSelected: boolean;
    onSelectAnnotation: (isSelected: boolean) => void;
    image: ImageData;
    width?: number;
    height?: number;
    status?: MEDIA_ANNOTATION_STATUS;
}

const THUMBNAIL_DIMENSIONS = {
    width: 78, // Plus 2px from borders
    height: 78,
};

export const AnnotationListItemThumbnail = memo(
    ({
        annotationShape,
        annotationId,
        isSelected,
        onSelectAnnotation,
        image,
        width = THUMBNAIL_DIMENSIONS.width,
        height = THUMBNAIL_DIMENSIONS.height,
        status = MEDIA_ANNOTATION_STATUS.NONE,
    }: AnnotationListItemThumbnailProps): JSX.Element => {
        const canvasRef = useRef<HTMLCanvasElement | null>(null);

        useEffect(() => {
            cropCanvasBasedOnShape(image, annotationShape, canvasRef.current);

            // eslint-disable-next-line react-hooks/exhaustive-deps
        }, []);
        return (
            <Flex
                alignItems='center'
                justifyContent='center'
                UNSAFE_className={`${classes.thumbnailWrapper} ${isSelected ? classes.isSelected : ''}`}
                UNSAFE_style={{ width, height, position: 'relative' }}
                data-testid={`annotation-${annotationId}-thumbnailWrapper`}
            >
                <canvas
                    id={`annotation-${annotationId}-thumbnail`}
                    data-testid={`annotation-${annotationId}-thumbnail`}
                    role='img'
                    aria-label={`Annotation ${annotationId}`}
                    aria-current={isSelected ? true : undefined}
                    style={{ objectFit: 'contain', width, height }}
                    ref={canvasRef}
                    onClick={() => onSelectAnnotation(!isSelected)}
                />

                <AnnotationStateIndicator id={`${annotationId}-status-`} state={status} />
            </Flex>
        );
    }
);
