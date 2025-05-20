// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Selector } from '@geti/ui/icons';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { SecondaryToolbar } from './secondary-toolbar.component';
import { SelectingStateProvider } from './selecting-state-provider.component';
import { SelectionToolContainer as Tool } from './selection-tool-container.component';

export const SelectingTool: ToolProps = {
    type: ToolType.SelectTool,
    label: ToolLabel.SelectTool,
    Icon: () => <Selector />,
    Tool,
    SecondaryToolbar,
    StateProvider: SelectingStateProvider,
    supportedDomains: [
        DOMAIN.CLASSIFICATION,
        DOMAIN.DETECTION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.ANOMALY_CLASSIFICATION,
        DOMAIN.ANOMALY_DETECTION,
        DOMAIN.ANOMALY_SEGMENTATION,
        DOMAIN.KEYPOINT_DETECTION,
    ],
};
