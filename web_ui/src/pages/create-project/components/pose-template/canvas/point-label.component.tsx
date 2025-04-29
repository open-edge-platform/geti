// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { useSelected } from '../../../../../providers/selected-provider/selected-provider.component';

interface PointLabelProps {
    point: KeypointNode;
}

export const PosePointLabel = ({ point }: PointLabelProps) => {
    const { isSelected } = useSelected();

    return (
        <div
            aria-label={`pose label ${point.label.name}`}
            style={{
                width: 'fit-content',
                color: 'var(--spectrum-global-color-static-black)',
                padding: 'var(--spectrum-global-dimension-size-75)',
                transform: 'scale(calc(1 / var(--zoom-level))) translate(calc(-100% - 6px), calc(-100% - 6px))',
                position: 'absolute',
                top: point.y,
                left: point.x,
                borderRadius: 4,
                transformOrigin: '0 0',
                backgroundColor: isSelected(point.label.id) ? 'rgb(255 255 255 / 88%)' : 'rgb(255 255 255 / 60%)',
            }}
        >
            {point.label.name}
        </div>
    );
};
