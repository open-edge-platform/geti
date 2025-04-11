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
