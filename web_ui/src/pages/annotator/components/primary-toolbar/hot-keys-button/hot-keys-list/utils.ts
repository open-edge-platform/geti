// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ToolType } from '../../../../core/annotation-tool-context.interface';
import { ToolProps } from '../../../../tools/tools.interface';

export const isToolAvailable = (tools: ToolProps[], expectedTool: ToolType): boolean =>
    !!tools.find((tool) => tool.type === expectedTool);
