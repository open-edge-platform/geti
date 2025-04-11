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
