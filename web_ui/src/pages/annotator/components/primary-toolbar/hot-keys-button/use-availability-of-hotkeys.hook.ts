// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo } from 'react';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { ToolType } from '../../../core/annotation-tool-context.interface';
import { HotKeyActions } from '../../../providers/annotator-provider/utils';
import { GrabcutToolType } from '../../../tools/grabcut-tool/grabcut-tool.enums';
import { PolygonMode } from '../../../tools/polygon-tool/polygon-tool.enum';
import { SelectingToolType } from '../../../tools/selecting-tool/selecting-tool.enums';
import { useAvailableTools } from '../../../tools/use-available-tools.hook';
import { isToolAvailable } from './hot-keys-list/utils';

export const useAvailabilityOfHotkeys = (domains: DOMAIN[]): Record<HotKeyActions, boolean> => {
    const availableTools = useAvailableTools(domains);

    const isBoundingBoxAvailable = isToolAvailable(availableTools, ToolType.BoxTool);
    const isRotatedBoundingBoxAvailable = isToolAvailable(availableTools, ToolType.RotatedBoxTool);
    const isCircleToolAvailable = isToolAvailable(availableTools, ToolType.CircleTool);
    const isPolygonToolAvailable = isToolAvailable(availableTools, ToolType.PolygonTool);
    const isGrabcutToolAvailable = isToolAvailable(availableTools, ToolType.GrabcutTool);
    const isWatershedToolAvailable = isToolAvailable(availableTools, ToolType.WatershedTool);
    const isSSIMToolAvailable = isToolAvailable(availableTools, ToolType.SSIMTool);
    const isRITMToolAvailable = isToolAvailable(availableTools, ToolType.RITMTool);
    const isExplanationToolAvailable = isToolAvailable(availableTools, ToolType.Explanation);

    return useMemo(
        () => ({
            saveAnnotations: true,
            selectAll: true,
            imageDrag: true,
            imageDragSecond: true,
            previousFrame: true,
            nextFrame: true,
            previous: true,
            next: true,
            playOrPause: true,
            delete: true,
            redo: true,
            undo: true,
            zoom: true,
            deselectAll: true,
            deleteSecond: true,
            redoSecond: true,
            copyAnnotation: true,
            pasteAnnotation: true,
            close: true,
            hideAllAnnotations: true,
            accept: true,
            [ToolType.EditTool]: false, // we do not have hotkey for edit tool
            [ToolType.SelectTool]: true,
            [SelectingToolType.SelectionTool]: false, // we do not have hotkey for selection tool
            [SelectingToolType.BrushTool]: false, // we do not have hotkey for brush tool
            [SelectingToolType.StampTool]: true,
            [PolygonMode.MagneticLasso]: isPolygonToolAvailable,
            [ToolType.RITMTool]: isRITMToolAvailable,
            [ToolType.SSIMTool]: isSSIMToolAvailable,
            [GrabcutToolType.BackgroundTool]: isGrabcutToolAvailable,
            [GrabcutToolType.ForegroundTool]: isGrabcutToolAvailable,
            [GrabcutToolType.InputTool]: isGrabcutToolAvailable,
            [ToolType.BoxTool]: isBoundingBoxAvailable,
            [ToolType.CircleTool]: isCircleToolAvailable,
            [ToolType.GrabcutTool]: isGrabcutToolAvailable,
            [ToolType.Explanation]: isExplanationToolAvailable,
            [ToolType.PolygonTool]: isPolygonToolAvailable,
            [ToolType.RotatedBoxTool]: isRotatedBoundingBoxAvailable,
            [ToolType.WatershedTool]: isWatershedToolAvailable,
            [ToolType.SegmentAnythingTool]: isToolAvailable(availableTools, ToolType.SegmentAnythingTool),
            [ToolType.KeypointTool]: false, // we do not have hotkey for keypoint detection
        }),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [domains]
    );
};
