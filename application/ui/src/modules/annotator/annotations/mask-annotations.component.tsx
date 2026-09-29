// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, useId } from 'react';

import type { Annotation } from '../../../shared/types';
import { AnnotationShapeWithoutLabels } from './annotation-shape-without-labels.component';

type MaskAnnotationsProps = {
    annotations: Annotation[];
    children: ReactNode;
    width: number;
    height: number;
    isEnabled: boolean;
};

export const MaskAnnotations = ({ annotations, children, width, height, isEnabled }: MaskAnnotationsProps) => {
    const id = useId();

    // Avoid building/compositing a full-image SVG mask (and duplicating every annotation) when unused.
    if (!isEnabled) {
        return <>{children}</>;
    }

    return (
        <>
            <mask id={`mask-${id}`}>
                <rect x='0' y='0' width={width} height={height} style={{ fill: 'white', fillOpacity: 1.0 }} />
                {annotations.map((annotation) => (
                    <g key={annotation.id} style={{ fill: 'black', fillOpacity: 1.0 }}>
                        <AnnotationShapeWithoutLabels annotation={annotation} />
                    </g>
                ))}
            </mask>
            <rect
                x={0}
                y={0}
                width={width}
                height={height}
                mask={`url(#mask-${id})`}
                pointerEvents={'none'}
                style={{ fillOpacity: 0.3, fill: 'black', strokeWidth: 0 }}
            />
            {children}
        </>
    );
};
