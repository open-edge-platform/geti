// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { BoundingBox } from '@geti/ui/icons';

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
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#bounding-box-tool',
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
