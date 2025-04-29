// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { useTaskChainOutput } from '../providers/task-chain-provider/use-task-chain-output.hook';
import { useTask } from '../providers/task-provider/task-provider.component';
import { filterForSelectedTask, filterHidden } from '../utils';

export const useVisibleAnnotations = (): Annotation[] => {
    const { tasks, selectedTask } = useTask();

    const outputAnnotations = useTaskChainOutput(tasks, selectedTask);

    return useMemo(() => {
        const visibleAnnotations = outputAnnotations
            .filter(filterHidden)
            .filter(filterForSelectedTask(selectedTask?.domain));

        return visibleAnnotations;
    }, [outputAnnotations, selectedTask]);
};
