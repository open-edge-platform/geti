// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AnnotationToolContext } from '../core/annotation-tool-context.interface';
import { useTask } from '../providers/task-provider/task-provider.component';
import { ToolProps } from './tools.interface';
import { useAvailableTools } from './use-available-tools.hook';

const useActiveTool = (annotationToolContext: AnnotationToolContext): undefined | ToolProps => {
    const { activeDomains } = useTask();
    const tools = useAvailableTools(activeDomains);

    return tools.find(({ type }: ToolProps) => type === annotationToolContext.tool);
};

export default useActiveTool;
