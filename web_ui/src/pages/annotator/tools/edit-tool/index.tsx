// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { EditTool as Tool } from './edit-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const EditTool: ToolProps = {
    type: ToolType.EditTool,
    label: ToolLabel.EditTool,
    Icon: () => <></>,
    Tool,
    SecondaryToolbar,
    StateProvider: ({ children }) => <>{children}</>,
    supportedDomains: [
        DOMAIN.CLASSIFICATION,
        DOMAIN.DETECTION,
        DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
        DOMAIN.SEGMENTATION,
        DOMAIN.SEGMENTATION_INSTANCE,
        DOMAIN.ANOMALY_CLASSIFICATION,
        DOMAIN.ANOMALY_DETECTION,
        DOMAIN.ANOMALY_SEGMENTATION,
    ],
};
