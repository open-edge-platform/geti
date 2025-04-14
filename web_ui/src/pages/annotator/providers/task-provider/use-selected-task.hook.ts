// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
