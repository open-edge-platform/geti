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

import { useId } from 'react-aria';

import { Annotation as AnnotationInterface } from '../../../core/annotations/annotation.interface';
import { ShapeFactory } from './shapes/factory.component';

import classes from './../annotator-canvas.module.scss';

const MASK_OPACITY = 0.4;

interface AnnotationMaskProps {
    annotations: AnnotationInterface[];
    width: number;
    height: number;
    fillOpacity?: number;
}

export const AnnotationsMask = ({
    annotations,
    width,
    height,
    fillOpacity = MASK_OPACITY,
}: AnnotationMaskProps): JSX.Element => {
    const maskId = useId();

    return (
        <svg
            id={`annotations-mask`}
            aria-label='Annotation mask'
            width={width}
            height={height}
            className={classes.layer}
        >
            <mask id={maskId}>
                <rect x='0' y='0' width={width} height={height} fill='white' fillOpacity={fillOpacity} />
                {annotations.map((annotation) => (
                    <g key={annotation.id} fill='black'>
                        {/* Use an empty set of labels so that the shape won't receive a background */}
                        <ShapeFactory annotation={{ ...annotation, labels: [] }} />
                    </g>
                ))}
            </mask>
            <rect x={0} y={0} width={width} height={height} mask={`url(#${maskId})`} color='black' />
        </svg>
    );
};
