// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { isPoseShape } from '../../../../core/annotations/utils';
import { ExpandablePointLabel } from '../../../create-project/components/pose-template/canvas/expandable-point-label.component';
import { Labels, LabelsProps } from './labels.component';

interface ShapeLabelProps extends LabelsProps {
    isOverlap?: boolean;
}

export const ShapeLabel = ({
    isOverlap,
    annotation,
    showOptions,
    areLabelsInteractive,
    annotationToolContext,
}: ShapeLabelProps) => {
    if (isPoseShape(annotation.shape)) {
        return annotation.shape.points.map((point) => (
            <ExpandablePointLabel isVisible key={point.label.id} point={point} isOverlap={isOverlap} />
        ));
    }

    return (
        <Labels
            isOverlap={isOverlap}
            showOptions={showOptions}
            annotation={annotation}
            areLabelsInteractive={areLabelsInteractive}
            annotationToolContext={annotationToolContext}
        />
    );
};
