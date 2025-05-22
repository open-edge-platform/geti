// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Watershed } from '@geti/ui/icons';

import ObjectColoringImg from '../../../../assets/primary-tools/object_coloring.webp';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { WATERSHED_SUPPORTED_DOMAINS } from './utils';
import { WatershedStateProvider } from './watershed-state-provider.component';
import { WatershedTool as Tool } from './watershed-tool.component';

export const WatershedTool: ToolProps = {
    type: ToolType.WatershedTool,
    label: ToolLabel.WatershedTool,
    Icon: () => <Watershed />,
    Tool,
    tooltip: {
        img: ObjectColoringImg,
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#object-coloring-tool',
        title: toolTypeToLabelMapping[ToolType.WatershedTool],
        description: 'Simply select the brush and draw over the objects you want to annotate.',
    },
    SecondaryToolbar,
    supportedDomains: WATERSHED_SUPPORTED_DOMAINS,
    StateProvider: WatershedStateProvider,
};
