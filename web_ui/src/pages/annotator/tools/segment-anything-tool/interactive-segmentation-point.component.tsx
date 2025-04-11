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

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { Circle } from '../../annotation/shapes/circle.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { InteractiveAnnotationPoint } from './segment-anything.interface';

interface InteractiveSegmentationPointProps extends InteractiveAnnotationPoint {
    isLoading: boolean;
}

export const InteractiveSegmentationPoint = ({
    x,
    y,
    positive,
    isLoading,
}: InteractiveSegmentationPointProps): JSX.Element => {
    const {
        zoomState: { zoom },
    } = useZoom();

    const fill = positive ? 'var(--brand-moss)' : 'var(--brand-coral-cobalt)';
    const radius = 1 / zoom;

    return (
        <>
            <Circle
                aria-label={`${positive ? 'Positive' : 'Negative'} interactive segmentation point`}
                shape={{ shapeType: ShapeType.Circle, x, y, r: 5 / zoom }}
                styles={{
                    fill,
                    opacity: 'var(--markers-opacity)',
                    strokeWidth: 'calc(1.5px / var(--zoom-level))',
                    stroke: 'var(--spectrum-global-color-static-gray-100)',
                }}
                data-testid={`point-${positive ? 'positive' : 'negative'}`}
            />
            {isLoading && (
                <g transform={`translate(${x}, ${y}) scale(${radius}, ${radius})`} aria-label='Processing input'>
                    <path d='M 0 -20 A 20 20 00 0 1 0 20' stroke='white' strokeWidth='3' fillOpacity='0'>
                        <animateTransform
                            attributeName='transform'
                            attributeType='XML'
                            type='rotate'
                            dur='1s'
                            from='0 0 0'
                            to='360 0 0'
                            repeatCount='indefinite'
                        />
                    </path>
                </g>
            )}
        </>
    );
};
