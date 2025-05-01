// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';
import { isNotCropDomain } from '@shared/utils';

import { Label } from '../../../../core/labels/label.interface';
import { filterOutEmptyLabel, isLocal } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { getPreviousTask } from '../task-chain-provider/utils';
import { useSelectedTask } from './use-selected-task.hook';

export interface TaskContextProps {
    tasks: Task[];
    selectedTask: null | Task;
    previousTask: null | Task;
    setSelectedTask: (task: Task | null) => void;
    defaultLabel: Label | null;
    setDefaultLabel: (label: Label | null) => void;
    isTaskChainDomainSelected: (domain: DOMAIN) => boolean;
    activeDomains: DOMAIN[];
    labels: Label[];
    isTaskChainSecondTask: boolean;
}
const TaskContext = createContext<TaskContextProps | undefined>(undefined);

const ALL_TASKS = 'All tasks';

interface TaskProviderProps {
    children: ReactNode;
}

export const TaskProvider = ({ children }: TaskProviderProps): JSX.Element => {
    const { project, isTaskChainProject } = useProject();

    const tasks = useMemo(() => {
        return project.tasks.filter(({ domain }) => domain !== undefined && isNotCropDomain(domain));
    }, [project]);

    const [selectedTask, setSelectedTask] = useSelectedTask(tasks);

    const [defaultLabelMap, setDefaultLabelMap] = useState<Record<string, Label | null>>({});

    const activeDomains = useMemo(() => {
        return selectedTask === null ? tasks.map(({ domain }) => domain) : [selectedTask.domain];
    }, [selectedTask, tasks]);

    const labels = useMemo(() => {
        return selectedTask === null ? tasks.flatMap((task) => task.labels) : selectedTask.labels;
    }, [selectedTask, tasks]);

    const isTaskChainDomainSelected = (domain: DOMAIN) => isTaskChainProject && selectedTask?.domain === domain;

    const isTaskChainSecondTask =
        isTaskChainDomainSelected(DOMAIN.CLASSIFICATION) || isTaskChainDomainSelected(DOMAIN.SEGMENTATION);

    const setDefaultLabel = (label: Label | null) => {
        // If the user selects a label while on "All Tasks", we assign a specific default
        // label for it, but it doesn't affect the default labels for other tasks
        if (!selectedTask) {
            setDefaultLabelMap({ ...defaultLabelMap, [ALL_TASKS]: label });
        } else {
            setDefaultLabelMap({ ...defaultLabelMap, [selectedTask.title]: label });
        }
    };

    useEffect(() => {
        const initialMap: Record<string, Label | null> = {};
        // Set the default labels for all the tasks upon mount
        tasks.forEach((task) => {
            const nonEmptyLabels = filterOutEmptyLabel(task.labels);
            const localLabels = nonEmptyLabels.filter(isLocal);
            const hasOnlyOneLabel = localLabels.length === 1;

            if (hasOnlyOneLabel) {
                // Assign the only label from this task as default
                initialMap[task.title] = localLabels[0];
            } else {
                // Or else, initialize it as null
                initialMap[task.title] = null;
            }
        });

        // If the task chain has only 1 local label, then we select that label,
        // this way in detection -> classification we always choose the detection label
        const localLabels = tasks.flatMap((task) => task.labels).filter(isLocal);
        if (localLabels.length === 1) {
            initialMap[ALL_TASKS] = localLabels[0];
        }

        setDefaultLabelMap(initialMap);

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const value = {
        tasks,
        selectedTask,
        setSelectedTask,
        setDefaultLabel,
        previousTask: getPreviousTask(tasks, selectedTask),
        defaultLabel: defaultLabelMap[selectedTask ? selectedTask.title : ALL_TASKS] ?? null,
        isTaskChainDomainSelected,
        labels,
        activeDomains,
        isTaskChainSecondTask,
    };

    return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
};

export const useTask = (): TaskContextProps => {
    const context = useContext(TaskContext);

    if (context === undefined) {
        throw new MissingProviderError('useTask', 'TaskProvider');
    }

    return context;
};
