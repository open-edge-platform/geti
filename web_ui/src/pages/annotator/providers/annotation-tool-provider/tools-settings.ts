// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { ToolsSettings, ToolType } from '../../core/annotation-tool-context.interface';
import { sensitivityConfig } from '../../tools/grabcut-tool/util';
import { defaultRITMConfig } from '../../tools/ritm-tool/ritm-tool.interface';
import { SelectingToolType } from '../../tools/selecting-tool/selecting-tool.enums';

export const DEFAULT_TOOLS_SETTINGS: ToolsSettings = new Map([
    [ToolType.SelectTool, { tool: SelectingToolType.SelectionTool, brushSize: null, stampedAnnotation: null }],
    [
        ToolType.CircleTool,
        {
            size: 20,
        },
    ],
    [
        ToolType.PolygonTool,
        {
            mode: null,
        },
    ],
    [
        ToolType.WatershedTool,
        {
            brushSize: 8,
            sensitivity: 1,
            label: undefined,
        },
    ],
    [
        ToolType.SSIMTool,
        {
            autoMergeDuplicates: true,
            shapeType: ShapeType.Rect,
            selectedLabel: undefined,
        },
    ],
    [
        ToolType.RITMTool,
        {
            dynamicBoxMode: defaultRITMConfig.dynamicBoxMode,
            rightClickMode: false,
            selectedLabel: undefined,
        },
    ],
    [
        ToolType.SegmentAnythingTool,
        {
            selectedLabel: undefined,
            maskOpacity: 0.3,
            interactiveMode: false,
            rightClickMode: false,
        },
    ],
    [
        ToolType.GrabcutTool,
        {
            selectedLabel: undefined,
            sensitivity: sensitivityConfig.default,
        },
    ],
]);
