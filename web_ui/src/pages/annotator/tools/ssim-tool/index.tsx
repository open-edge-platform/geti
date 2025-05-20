// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DetectionTool } from '@geti/ui/icons';

import SSIMImg from '../../../../assets/primary-tools/ssim.webp';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { SSIMStateProvider } from './ssim-state-provider.component';
import { SSIMTool as Tool } from './ssim-tool.component';
import { SSIM_SUPPORTED_DOMAINS } from './util';

export const SSIMTool: ToolProps = {
    type: ToolType.SSIMTool,
    label: ToolLabel.SSIMTool,
    Icon: () => <DetectionTool />,
    Tool,
    SecondaryToolbar,
    supportedDomains: SSIM_SUPPORTED_DOMAINS,
    tooltip: {
        img: SSIMImg,
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#detection-assistant-tool',
        title: toolTypeToLabelMapping[ToolType.SSIMTool],
        description:
            'Draw a box or a circle over an object and the system will mark all objects similar to the ' +
            'one you annotated.',
    },
    StateProvider: SSIMStateProvider,
};
