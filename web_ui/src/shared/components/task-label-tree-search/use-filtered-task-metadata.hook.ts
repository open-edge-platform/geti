// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import isEmpty from 'lodash/isEmpty';
import { useFilter } from 'react-aria';

import { findLabelParents, uniqueLabels } from '../../../core/labels/annotator-utils/labels-utils';
import { getTasksMetadata } from '../../../pages/project-details/components/project-labels/utils';
import { isNonEmptyArray } from '../../utils';
import { Label } from './../../../core/labels/label.interface';
import { Task, TaskMetadata } from './../../../core/projects/task.interface';

type LabelFilter = <T extends { name: string }>(labels: T[]) => T[];

const getFilteredTaskMetadata = (
    tasks: Task[],
    input: string,
    labelsFilter: LabelFilter,
    includesEmptyLabels: boolean
) => {
    const emptyInput = isEmpty(input.trim());
    const isTaskChainFirstTask = (index: number) => index === 0 && tasks.length > 1;

    // For task chain, the first task label is the second task labels 'parentLabelId',
    // as a root label it can't be removed/filtered and thus, we return the task as it is.
    const filteredTasksLabels = tasks
        .map((task, index) => {
            if (isTaskChainFirstTask(index) || emptyInput) {
                return task;
            }

            const matchLabels = labelsFilter(task.labels);
            const parents: Label[] = matchLabels.flatMap((label: Label) => findLabelParents(task.labels, label));

            return { ...task, labels: uniqueLabels(matchLabels.concat(parents)) };
        })
        .filter(({ labels }) => isNonEmptyArray(labels));

    return getTasksMetadata(filteredTasksLabels, includesEmptyLabels);
};

interface useFilteredTaskMetadataProps {
    input: string;
    tasks: Task[];
    selectedTask: Task | null;
    includesEmptyLabels?: boolean;
}

export const useFilteredTaskMetadata = ({
    input,
    tasks,
    selectedTask,
    includesEmptyLabels = true,
}: useFilteredTaskMetadataProps) => {
    const { contains } = useFilter({ sensitivity: 'base' });

    return useMemo((): TaskMetadata[] => {
        const labelsFilter: LabelFilter = (labels) => labels.filter((label) => contains(label.name, input));

        const isTaskChain = tasks.length > 1;
        const emptyInput = isEmpty(input.trim());
        const filteredTasksMetadata = getFilteredTaskMetadata(tasks, input, labelsFilter, includesEmptyLabels);

        if (!isTaskChain) {
            return filteredTasksMetadata;
        }

        const isFirstTaskSelected = tasks[0].id === selectedTask?.id;
        const isSecondTaskSelected = tasks[1].id === selectedTask?.id;

        const [firstTask, ...otherTasks] = filteredTasksMetadata;
        const filteredFirstTask = { ...firstTask, labels: labelsFilter(firstTask.labels) };

        if (isFirstTaskSelected) {
            return isNonEmptyArray(filteredFirstTask.labels) ? [filteredFirstTask] : [];
        }

        if (isSecondTaskSelected) {
            return otherTasks;
        }

        if (isNonEmptyArray(filteredFirstTask.labels) || emptyInput) {
            return [filteredFirstTask, ...otherTasks];
        }

        return otherTasks;

        // "contains" changes on every render
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [input, tasks]);
};
