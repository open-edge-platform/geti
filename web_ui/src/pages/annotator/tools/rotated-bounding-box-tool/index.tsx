// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RotatedBox } from '../../../../assets/icons';
import RotatedDetectionImg from '../../../../assets/primary-tools/rotated_detection.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { RotatedBoundingBoxTool as Tool } from './rotated-bounding-box-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const RotatedBoundingBoxTool: ToolProps = {
    type: ToolType.RotatedBoxTool,
    label: ToolLabel.RotatedBoxTool,
    Icon: () => <RotatedBox />,
    Tool,
    SecondaryToolbar,
    StateProvider: ({ children }) => <>{children}</>,
    tooltip: {
        img: RotatedDetectionImg,
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#bounding-box-tool',
        title: toolTypeToLabelMapping[ToolType.RotatedBoxTool],
        description: `The tool intended for object detection task.
         A rotated bounding box acts as a normal bounding box, but it can be rotated to fit the object better.`,
    },
    supportedDomains: [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX],
};
