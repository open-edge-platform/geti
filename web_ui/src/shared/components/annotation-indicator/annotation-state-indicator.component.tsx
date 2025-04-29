// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_ANNOTATION_STATUS } from '../../../core/media/base.interface';
import { useProject } from '../../../pages/project-details/providers/project-provider/project-provider.component';
import { StateIndicator } from './state-indicator.component';
import {
    ANNOTATED_IMAGE_TOOLTIP,
    ANNOTATED_IMAGE_TOOLTIP_ANOMALY,
    ANNOTATED_IMAGE_TOOLTIP_TC,
    PARTIALLY_ANNOTATED_IMAGE_TOOLTIP_TC,
    TO_REVISIT_IMAGE_TOOLTIP,
    TO_REVISIT_IMAGE_TOOLTIP_TC,
} from './utils';

interface AnnotationStateIndicatorProps {
    state: MEDIA_ANNOTATION_STATUS;
    id: string;
}

export const AnnotationStateIndicator = ({ state, id }: AnnotationStateIndicatorProps): JSX.Element => {
    const { isTaskChainProject } = useProject();

    return (
        <StateIndicator
            id={id}
            state={state}
            annotatedTooltip={isTaskChainProject ? ANNOTATED_IMAGE_TOOLTIP_TC : ANNOTATED_IMAGE_TOOLTIP}
            partiallyAnnotatedTooltip={
                isTaskChainProject ? PARTIALLY_ANNOTATED_IMAGE_TOOLTIP_TC : ANNOTATED_IMAGE_TOOLTIP_ANOMALY
            }
            revisitTooltip={isTaskChainProject ? TO_REVISIT_IMAGE_TOOLTIP_TC : TO_REVISIT_IMAGE_TOOLTIP}
        />
    );
};
