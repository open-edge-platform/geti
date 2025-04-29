// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useTask } from '../../providers/task-provider/task-provider.component';

export const useTaskLabels = () => {
    const { selectedTask, tasks } = useTask();
    return useMemo(() => {
        if (selectedTask === null) {
            return tasks.flatMap(({ labels }) => labels);
        }
        return selectedTask.labels;
    }, [selectedTask, tasks]);
};
