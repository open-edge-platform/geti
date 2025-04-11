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

import { Watershed } from '../../../../assets/icons';
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
        url: 'guide/annotations/annotation-tools.html#object-coloring-tool',
        title: toolTypeToLabelMapping[ToolType.WatershedTool],
        description: 'Simply select the brush and draw over the objects you want to annotate.',
    },
    SecondaryToolbar,
    supportedDomains: WATERSHED_SUPPORTED_DOMAINS,
    StateProvider: WatershedStateProvider,
};
