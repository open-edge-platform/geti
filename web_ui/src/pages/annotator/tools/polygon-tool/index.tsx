// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Polygon } from '@geti/ui/icons';

import PolygonImg from '../../../../assets/primary-tools/polygon.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { PolygonStateProvider } from './polygon-state-provider.component';
import { PolygonTool as Tool } from './polygon-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const PolygonTool: ToolProps = {
    type: ToolType.PolygonTool,
    label: ToolLabel.PolygonTool,
    Icon: () => <Polygon />,
    Tool,
    SecondaryToolbar,
    tooltip: {
        img: PolygonImg,
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#polygon-tool',
        title: toolTypeToLabelMapping[ToolType.PolygonTool],
        description: `The polygon tool allows for free form drawing around shapes.`,
    },
    supportedDomains: [DOMAIN.SEGMENTATION, DOMAIN.SEGMENTATION_INSTANCE, DOMAIN.ANOMALY_SEGMENTATION],
    StateProvider: PolygonStateProvider,
};
