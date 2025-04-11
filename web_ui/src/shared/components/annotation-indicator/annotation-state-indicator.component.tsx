// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
