// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FunctionComponent, PropsWithChildren } from 'react';

import { Explanation } from '@geti/ui/icons';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolAnnotationContextProps, ToolProps } from '../tools.interface';
import { ExplanationSecondaryToolbar } from './explanation-secondary-toolbar.component';

export const ExplanationTool: ToolProps = {
    type: ToolType.Explanation,
    label: ToolLabel.Explanation,
    Icon: () => <Explanation />,
    Tool: () => <></>,
    SecondaryToolbar: ExplanationSecondaryToolbar as FunctionComponent<PropsWithChildren<ToolAnnotationContextProps>>,
    StateProvider: ({ children }) => <>{children}</>,
    supportedDomains: [
        DOMAIN.DETECTION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.ANOMALY_DETECTION,
        DOMAIN.ANOMALY_SEGMENTATION,
        DOMAIN.ANOMALY_CLASSIFICATION,
        DOMAIN.CLASSIFICATION,
        DOMAIN.KEYPOINT_DETECTION,
    ],
};
