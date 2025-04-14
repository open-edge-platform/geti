// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, RefObject } from 'react';

import { default as ClipperShape } from '@doodle3d/clipper-js';
import isEmpty from 'lodash/isEmpty';

import { Annotation, RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { Point, Shape } from '../../../../core/annotations/shapes.interface';
import { getTheTopShapeAt, isPolygon } from '../../../../core/annotations/utils';
import { hasEqualSize } from '../../../../shared/utils';
import { getRelativePoint } from '../../../utils';
import { transformToClipperShape } from '../utils';

// We set min to 3px because clipper-js does not work with properly with value less than 3px.
export const MIN_BRUSH_SIZE = 3;

export const getBrushMaxSize = (size: RegionOfInterest): number => Math.round(Math.max(size.width, size.height) * 0.15);

export const pointInShape = (annotations: Annotation[], point: Point, shiftKey: boolean): Annotation[] => {
    const topAnnotation = getTheTopShapeAt(annotations, point);

    if (topAnnotation) {
        return annotations.map((annotation: Annotation) => {
            if (annotation.id === topAnnotation.id) {
                return {
                    ...annotation,
                    isSelected: !annotation.isSelected,
                };
            }
            return shiftKey ? annotation : { ...annotation, isSelected: false };
        });
    }

    return annotations.map((annotation: Annotation) => ({ ...annotation, isSelected: false }));
};

export const getIntersectedAnnotationsIds = (annotations: Annotation[], shape: Shape): string[] => {
    const subject: ClipperShape = transformToClipperShape(shape);
    let clip: ClipperShape | null = null;
    return annotations.reduce<string[]>((prev, annotation: Annotation) => {
        const { shape: annotationShape, isHidden } = annotation;

        if (isHidden) {
            return prev;
        }

        clip = transformToClipperShape(annotationShape);

        if (clip) {
            const result: ClipperShape = subject.intersect(clip);
            if (!isEmpty(result.paths)) {
                return [...prev, annotation.id];
            }
        }

        return prev;
    }, []);
};

export const areAnnotationsIdentical = (prevAnnotations: Annotation[], currAnnotations: Annotation[]): boolean => {
    const filteredAnnotations = prevAnnotations.filter(
        (annotation: Annotation, index: number) => annotation.isSelected === currAnnotations[index].isSelected
    );
    return hasEqualSize(filteredAnnotations, prevAnnotations);
};

export const calcRelativePoint =
    (zoom: number, element?: RefObject<SVGRectElement>) =>
    <T>(callback: (point: Point) => T) =>
    (event: PointerEvent<SVGSVGElement>): void | T => {
        if (element?.current) {
            return callback(getRelativePoint(element.current, { x: event.clientX, y: event.clientY }, zoom));
        }
    };

export const getSelectedPolygonAnnotations = (annotations: Annotation[]): Annotation[] =>
    annotations.filter(({ isSelected, shape }) => isSelected && isPolygon(shape));
