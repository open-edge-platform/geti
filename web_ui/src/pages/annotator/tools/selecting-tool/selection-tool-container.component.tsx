// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ToolAnnotationContextProps } from '../tools.interface';
import { BrushTool } from './components/brush-tool.component';
import { useSelectingState } from './selecting-state-provider.component';
import { SelectingTool } from './selecting-tool.component';
import { SelectingToolType } from './selecting-tool.enums';
import { StampTool } from './stamp-tool/stamp-tool.component';

export const SelectionToolContainer = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { activeTool, brushSize, isBrushSizePreviewVisible } = useSelectingState();

    return (
        <>
            {activeTool === SelectingToolType.StampTool && <StampTool annotationToolContext={annotationToolContext} />}
            {activeTool === SelectingToolType.SelectionTool && (
                <SelectingTool annotationToolContext={annotationToolContext} />
            )}
            {activeTool === SelectingToolType.BrushTool && (
                <BrushTool
                    brushSize={brushSize}
                    showCirclePreview={isBrushSizePreviewVisible}
                    annotationToolContext={annotationToolContext}
                />
            )}
        </>
    );
};
