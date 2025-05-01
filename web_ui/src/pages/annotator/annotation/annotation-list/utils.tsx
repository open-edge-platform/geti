// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { runWhenTruthy } from '@shared/utils';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getBoundingBox } from '../../../../core/annotations/math';
import { Shape } from '../../../../core/annotations/shapes.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';

export const reorder = (annotations: Annotation[], startIndex: number, endIndex: number): Annotation[] => {
    const newAnnotations = [...annotations];
    const [draggedAnnotation] = newAnnotations.splice(startIndex, 1);

    newAnnotations.splice(endIndex, 0, draggedAnnotation);

    return newAnnotations.reverse().map((annotation: Annotation, index) => ({ ...annotation, zIndex: index }));
};

export const cropCanvasBasedOnShape = runWhenTruthy(
    (image: ImageData, annotationShape: Shape, destinationCanvas: HTMLCanvasElement): void => {
        // Create a temporary canvas and "inject" the ImageData
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');

        if (!tempCtx) return;

        tempCanvas.width = image.width;
        tempCanvas.height = image.height;

        tempCtx.putImageData(image, 0, 0);

        const ctx = destinationCanvas.getContext('2d');

        if (ctx === null) {
            return;
        }

        const pixelRatio = window.devicePixelRatio;
        const crop = getBoundingBox(annotationShape);

        // Resize the destination canvas based the shape's bounding box
        destinationCanvas.width = crop.width * pixelRatio;
        destinationCanvas.height = crop.height * pixelRatio;

        ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        ctx.imageSmoothingQuality = 'high';

        // Draw the cropped image from tempCanvas to destinationCanvas
        ctx.drawImage(tempCanvas, crop.x, crop.y, crop.width, crop.height, 0, 0, crop.width, crop.height);
    }
);

export const NOTIFICATION_MESSAGE: Partial<Record<DOMAIN, string>> = {
    [DOMAIN.CLASSIFICATION]: 'Nothing to classify. Draw bounding boxes on objects for classification.',
    [DOMAIN.SEGMENTATION]: 'Nothing to segment. Draw bounding boxes on objects for segmentation.',
};
