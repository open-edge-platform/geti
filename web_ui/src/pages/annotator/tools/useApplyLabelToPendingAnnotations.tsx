// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Label } from '../../../core/labels/label.interface';
import { isEmptyLabel } from '../../../core/labels/utils';
import { AnnotationToolContext, ToolType } from '../core/annotation-tool-context.interface';

// For some smart tools, we have an intermediate step, which happens when the user
// uses the tools and the algorithm returns an annotation. This annotation needs to be
// accepted/reject by the user using the "confirm/reject" buttons.
// But in the case that the user selects a label during this step, we want to automatically
// accept the annotation. That is the reason for this hook.

interface UseApplyLabelToPendingAnnotations {
    applyAnnotations: (label: Label | undefined) => void;
    annotationToolContext: AnnotationToolContext;
    tool: ToolType.RITMTool | ToolType.SSIMTool | ToolType.GrabcutTool | ToolType.SegmentAnythingTool;
}

export const useApplyLabelToPendingAnnotations = ({
    applyAnnotations,
    annotationToolContext,
    tool,
}: UseApplyLabelToPendingAnnotations): void => {
    const { getToolSettings, updateToolSettings } = annotationToolContext;

    const toolSettings = getToolSettings(tool);

    useEffect(() => {
        const isNoEmptyLabel = toolSettings.selectedLabel && !isEmptyLabel(toolSettings.selectedLabel);

        if (isNoEmptyLabel) {
            applyAnnotations(toolSettings.selectedLabel);
            updateToolSettings(tool, { selectedLabel: undefined });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [toolSettings]);
};
