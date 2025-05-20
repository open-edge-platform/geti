// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { memo, useEffect, useRef } from 'react';

import { Flex } from '@geti/ui';

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
