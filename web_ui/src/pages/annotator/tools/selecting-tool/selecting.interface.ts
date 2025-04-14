// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Polygon } from '../../../../core/annotations/shapes.interface';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { Hotkeys } from '../../providers/annotator-provider/utils';
import { SelectingToolType } from './selecting-tool.enums';

// TODO: We don't have hotkey definitions for all of tools yet
export const SelectingHotKeys: Pick<Hotkeys, SelectingToolType> = {
    [SelectingToolType.BrushTool]: '',
    [SelectingToolType.SelectionTool]: '',
    [SelectingToolType.StampTool]: 's',
};

export interface BrushToolProps {
    brushSize: number;
    showCirclePreview: boolean;
    annotationToolContext: AnnotationToolContext;
}

export interface GhostPolygon {
    shape: Polygon;
    annotationId?: string;
}
