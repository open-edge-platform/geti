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

import { MagicWandIcon } from '../../../../assets/icons';
import RITMImg from '../../../../assets/primary-tools/ritm.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { RITMStateProvider } from './ritm-state-provider.component';
import { RITMTool as Tool } from './ritm-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const RITMTool: ToolProps = {
    type: ToolType.RITMTool,
    label: ToolLabel.RITMTool,
    Icon: () => <MagicWandIcon />,
    Tool,
    SecondaryToolbar,
    supportedDomains: [
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.ANOMALY_SEGMENTATION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
    ],
    tooltip: {
        img: RITMImg,
        url: 'guide/annotations/annotation-tools.html#interactive-segmentation',
        title: toolTypeToLabelMapping[ToolType.RITMTool],
        description: 'Left-click on an object to draw a polygon around it.',
    },
    StateProvider: RITMStateProvider,
};
