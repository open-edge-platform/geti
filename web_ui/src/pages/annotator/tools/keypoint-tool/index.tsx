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

import { KeypointDetection } from '../../../../assets/icons';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { KeypointStateProvider } from './keypoint-state-provider.component';
import { KeypointTool as Tool } from './keypoint-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const KeypointTool: ToolProps = {
    type: ToolType.KeypointTool,
    label: ToolLabel.KeypointTool,
    Icon: () => <KeypointDetection />,
    Tool,
    SecondaryToolbar,
    StateProvider: KeypointStateProvider,
    supportedDomains: [DOMAIN.KEYPOINT_DETECTION],
};
