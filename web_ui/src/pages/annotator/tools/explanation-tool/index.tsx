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

import { FunctionComponent, PropsWithChildren } from 'react';

import { Explanation } from '../../../../assets/icons';
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
