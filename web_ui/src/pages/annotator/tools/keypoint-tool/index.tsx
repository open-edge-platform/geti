// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeypointDetection } from '../../../../assets/icons';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { KeypointStateProvider } from './keypoint-state-provider.component';
import { KeypointTool as Tool } from './keypoint-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const KeypointTool: ToolProps = {
    type: ToolType.KeypointTool,
    label: ToolLabel.KeypointTool,
    Icon: () => <KeypointDetection />,
    Tool,
    SecondaryToolbar,
    StateProvider: KeypointStateProvider,
    supportedDomains: [DOMAIN.KEYPOINT_DETECTION],
};
