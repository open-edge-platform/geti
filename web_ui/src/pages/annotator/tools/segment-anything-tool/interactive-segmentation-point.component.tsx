// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
