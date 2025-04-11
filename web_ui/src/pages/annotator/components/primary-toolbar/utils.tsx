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

import { useEffect } from 'react';

import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';

import { hasMaxAllowedAnnotations } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { AnnotationToolContext, ToolType } from '../../core/annotation-tool-context.interface';
import { getFilterAnnotationByTask, getPreviousTask } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { ToolProps } from '../../tools/tools.interface';
import { useAvailableTools } from '../../tools/use-available-tools.hook';

export const shouldDisableTools = (
    annotationToolContext: AnnotationToolContext,
    tasks: Task[],
    selectedTask: null | Task
): boolean => {
    const { scene } = annotationToolContext;

    const isTaskChainProject = !isEmpty(tasks);

    // If it's not a task chain project, the rest of the verification is unnecessary
    if (!isTaskChainProject) {
        return false;
    }

    const previousTask = getPreviousTask(tasks, selectedTask);

    if (!isNil(previousTask)) {
        const annotationsFromPreviousTask = scene.annotations.filter(getFilterAnnotationByTask(previousTask));

        // If the user is on the second task and the first one has no annotations (output)
        return isEmpty(annotationsFromPreviousTask);
    }

    return false;
};

export const useDrawingTools = (activeDomains: DOMAIN[]): ToolProps[] => {
    const tools = useAvailableTools(activeDomains);

    return tools.filter(({ type }: ToolProps) => ![ToolType.SelectTool, ToolType.Explanation].includes(type));
};

export const useDisabledTools = (annotationToolContext: AnnotationToolContext): boolean => {
    const { tasks, selectedTask } = useTask();
    const isDisabled =
        hasMaxAllowedAnnotations(annotationToolContext.scene.annotations) ||
        shouldDisableTools(annotationToolContext, tasks, selectedTask);

    useEffect(() => {
        // hide all the tools and toggle the SelectTool
        if (isDisabled && annotationToolContext.tool !== ToolType.SelectTool) {
            annotationToolContext.toggleTool(ToolType.SelectTool);
        }
    }, [annotationToolContext, isDisabled]);

    return isDisabled;
};
