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

import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { EditTool as Tool } from './edit-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const EditTool: ToolProps = {
    type: ToolType.EditTool,
    label: ToolLabel.EditTool,
    Icon: () => <></>,
    Tool,
    SecondaryToolbar,
    StateProvider: ({ children }) => <>{children}</>,
    supportedDomains: [
        DOMAIN.CLASSIFICATION,
        DOMAIN.DETECTION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.ANOMALY_CLASSIFICATION,
        DOMAIN.ANOMALY_DETECTION,
        DOMAIN.ANOMALY_SEGMENTATION,
    ],
};
