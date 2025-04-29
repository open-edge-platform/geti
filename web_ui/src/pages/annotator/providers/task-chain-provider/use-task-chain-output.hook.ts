// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Task } from '../../../../core/projects/task.interface';
import { useOutputAnnotationsFilter } from '../../annotation/annotation-filter/use-output-annotations-filter.hook';
import { useTaskChain } from './task-chain-provider.component';
import { getTaskChainOutput } from './utils';

// NOTE: this hook might be refactored later on
export const useTaskChainOutput = (tasks: Task[], selectedTask: Task | null): Annotation[] => {
    const { inputs, outputs } = useTaskChain();

    const taskChainOutput = useMemo(
        () => getTaskChainOutput(inputs, outputs, tasks, selectedTask),
        [inputs, outputs, tasks, selectedTask]
    );

    return useOutputAnnotationsFilter(taskChainOutput);
};
