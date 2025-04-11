// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { useSelected } from '../../../../annotator/providers/selected-provider/selected-provider.component';

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
