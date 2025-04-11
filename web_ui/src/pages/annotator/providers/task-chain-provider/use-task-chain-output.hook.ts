// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
