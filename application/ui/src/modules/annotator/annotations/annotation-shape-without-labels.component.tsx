// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Annotation } from '../../../shared/types';
import { useAnnotationVisibility } from '../annotation-visibility-provider.component';
import { AnnotationShape } from './annotation-shape/annotation-shape.component';

interface AnnotationShapeWithoutLabelsProps {
    annotation: Annotation;
}

export const AnnotationShapeWithoutLabels = ({ annotation }: AnnotationShapeWithoutLabelsProps) => {
    const { isVisible } = useAnnotationVisibility();
    const { shape } = annotation;

    if (shape.type === 'rectangle') {
        return (
            <g transform={`translate(${shape.x}, ${shape.y})`} display={isVisible ? 'block' : 'none'}>
                <AnnotationShape annotation={{ ...annotation, shape: { ...shape, x: 0, y: 0 } }} />
            </g>
        );
    }

    return <AnnotationShape annotation={annotation} />;
};
