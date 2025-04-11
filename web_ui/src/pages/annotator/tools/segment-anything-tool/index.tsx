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

import { SegmentAnythingIcon } from '../../../../assets/icons';
import RITMImg from '../../../../assets/primary-tools/ritm.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { SegmentAnythingStateProvider } from './segment-anything-state-provider.component';
import { SegmentAnythingTool as Tool } from './segment-anything-tool.component';

export const SegmentAnythingTool: ToolProps = {
    type: ToolType.SegmentAnythingTool,
    label: ToolLabel.SegmentAnythingTool,
    Icon: () => <SegmentAnythingIcon />,
    Tool,
    SecondaryToolbar,
    supportedDomains: [
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.DETECTION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
        DOMAIN.ANOMALY_SEGMENTATION,
        DOMAIN.ANOMALY_DETECTION,
    ],
    tooltip: {
        img: RITMImg,
        url: 'guide/annotations/annotation-tools.html#automatic-segmentation',
        title: toolTypeToLabelMapping[ToolType.SegmentAnythingTool],
        description: 'Click on an object to draw a shape around it. Shift-click to subtract or add parts.',
    },
    StateProvider: SegmentAnythingStateProvider,
};
