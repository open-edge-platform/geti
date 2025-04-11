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

import { DetectionTool } from '../../../../assets/icons';
import SSIMImg from '../../../../assets/primary-tools/ssim.webp';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { SSIMStateProvider } from './ssim-state-provider.component';
import { SSIMTool as Tool } from './ssim-tool.component';
import { SSIM_SUPPORTED_DOMAINS } from './util';

export const SSIMTool: ToolProps = {
    type: ToolType.SSIMTool,
    label: ToolLabel.SSIMTool,
    Icon: () => <DetectionTool />,
    Tool,
    SecondaryToolbar,
    supportedDomains: SSIM_SUPPORTED_DOMAINS,
    tooltip: {
        img: SSIMImg,
        url: 'guide/annotations/annotation-tools.html#detection-assistant',
        title: toolTypeToLabelMapping[ToolType.SSIMTool],
        description:
            'Draw a box or a circle over an object and the system will mark all objects similar to the ' +
            'one you annotated.',
    },
    StateProvider: SSIMStateProvider,
};
