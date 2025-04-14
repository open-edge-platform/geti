// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
