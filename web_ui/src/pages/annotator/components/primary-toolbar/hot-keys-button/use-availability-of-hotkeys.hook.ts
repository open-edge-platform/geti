// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
