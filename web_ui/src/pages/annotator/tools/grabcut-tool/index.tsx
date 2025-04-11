// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { QuickSelection } from '../../../../assets/icons';
import QuickSelectionImg from '../../../../assets/primary-tools/quick_selection.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { GrabcutStateProvider } from './grabcut-state-provider.component';
import { GrabcutTool as Tool } from './grabcut-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const GrabcutTool: ToolProps = {
    Tool,
    type: ToolType.GrabcutTool,
    label: ToolLabel.GrabcutTool,
    StateProvider: GrabcutStateProvider,
    supportedDomains: [DOMAIN.SEGMENTATION, DOMAIN.SEGMENTATION_INSTANCE, DOMAIN.ANOMALY_SEGMENTATION],
    tooltip: {
        img: QuickSelectionImg,
        url: 'guide/annotations/annotation-tools.html#quick-selection-tool',
        title: toolTypeToLabelMapping[ToolType.GrabcutTool],
        description: `Simply draw a rectangle around the object and Intel® Geti™ will fit a 
            polygon to the shape of the object.`,
    },
    Icon: () => <QuickSelection />,
    SecondaryToolbar: ({ annotationToolContext }) => <SecondaryToolbar annotationToolContext={annotationToolContext} />,
};
