// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ToolType } from '../../core/annotation-tool-context.interface';

export interface PrimaryToolbarButtonProps {
    activeTool: ToolType;
    setActiveTool: (tool: ToolType) => void;
}
