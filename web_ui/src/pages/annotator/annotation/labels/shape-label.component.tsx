// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
