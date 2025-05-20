// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SegmentAnythingIcon } from '@geti/ui/icons';

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
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#automatic-segmentation-tool',
        title: toolTypeToLabelMapping[ToolType.SegmentAnythingTool],
        description: 'Click on an object to draw a shape around it. Shift-click to subtract or add parts.',
    },
    StateProvider: SegmentAnythingStateProvider,
};
