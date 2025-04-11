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

import { useCallback, useMemo } from 'react';

import { useSearchParams } from 'react-router-dom';

import { Task } from '../../../../core/projects/task.interface';
import { hasEqualId } from '../../../../shared/utils';

type UseSelectedTask = [null | Task, (task: Task | null) => void];

export const useSelectedTask = (tasks: Task[]): UseSelectedTask => {
    const [searchParams, setSearchParams] = useSearchParams();
    const selectedTaskId = searchParams.get('task-id');

    // For single tasks we ignore the parameter
    const selectedTask = useMemo(() => {
        return tasks.length === 1 ? tasks[0] : (tasks.find(hasEqualId(selectedTaskId)) ?? null);
    }, [tasks, selectedTaskId]);

    const setSelectedTask = useCallback(
        (task: Task | null) => {
            if (task === null) {
                searchParams.delete('task-id');
            } else {
                searchParams.set('task-id', task.id);
            }
            searchParams.delete('annotation-filter');
            setSearchParams(searchParams);
        },
        [searchParams, setSearchParams]
    );

    return [selectedTask, setSelectedTask];
};
