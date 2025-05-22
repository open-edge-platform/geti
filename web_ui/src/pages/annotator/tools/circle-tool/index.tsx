// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { BoundingCircle } from '@geti/ui/icons';

import CircleImg from '../../../../assets/primary-tools/circle.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { CircleStateProvider } from './circle-state-provider.component';
import { CircleTool as Tool } from './circle-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const CircleTool: ToolProps = {
    type: ToolType.CircleTool,
    label: ToolLabel.CircleTool,
    Icon: () => <BoundingCircle />,
    Tool,
    SecondaryToolbar,
    tooltip: {
        img: CircleImg,
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#circle-tool',
        title: toolTypeToLabelMapping[ToolType.CircleTool],
        description: `Its purpose is to simplify annotation of circular objects.`,
    },
    StateProvider: CircleStateProvider,
    supportedDomains: [DOMAIN.SEGMENTATION, DOMAIN.SEGMENTATION_INSTANCE, DOMAIN.ANOMALY_SEGMENTATION],
};
