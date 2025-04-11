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

import { BoundingBox } from '../../../../assets/icons';
import DetectionImg from '../../../../assets/primary-tools/detection.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { BoundingBoxTool as Tool } from './bounding-box-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const BoundingBoxTool: ToolProps = {
    type: ToolType.BoxTool,
    label: ToolLabel.BoxTool,
    Icon: () => <BoundingBox />,
    Tool,
    SecondaryToolbar,
    tooltip: {
        img: DetectionImg,
        url: 'guide/annotations/annotation-tools.html#bounding-box-tool',
        title: toolTypeToLabelMapping[ToolType.BoxTool],
        description: `The tool intended for object detection task. A bounding box is a rectangle surrounding
        an object in an image.`,
    },
    StateProvider: ({ children }) => <>{children}</>,
    supportedDomains: [
        DOMAIN.DETECTION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.ANOMALY_DETECTION,
        DOMAIN.ANOMALY_SEGMENTATION,
    ],
};
