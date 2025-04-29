// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isNil from 'lodash/isNil';

import { useProjectStatus } from '../../../core/projects/hooks/use-project-status.hook';
import { RequiredAnnotationsDetailsEntry } from '../../../core/projects/project-status.interface';
import { Task } from '../../../core/projects/task.interface';
import { hasEqualId } from '../../../shared/utils';
import { useProject } from '../../project-details/providers/project-provider/project-provider.component';
import { getTaskRequiredAnnotationsDetails } from '../providers/task-provider/utils';

export interface TaskRequiredAnnotations {
    title: string;
    value: number;
    details: RequiredAnnotationsDetailsEntry[];
    newAnnotations: number;
    isAutoTraining?: boolean;
}

export const useRequiredAnnotations = (selectedTask: Task | null): TaskRequiredAnnotations[] => {
    const { projectIdentifier } = useProject();
    const { data: projectStatus } = useProjectStatus(projectIdentifier);

    const projectTasks = projectStatus?.tasks ?? [];

    if (isNil(selectedTask)) {
        return projectTasks.map((projectTask) => ({
            title: projectTask.title,
            value: projectTask.required_annotations.value,
            newAnnotations: projectTask.n_new_annotations,
            details: getTaskRequiredAnnotationsDetails(projectTask),
        }));
    }

    const currentTaskStatus = projectTasks.find(hasEqualId(selectedTask.id));

    return [
        {
            title: currentTaskStatus?.title ?? '',
            details: getTaskRequiredAnnotationsDetails(currentTaskStatus, selectedTask),
            value: currentTaskStatus?.required_annotations.value ?? 0,
            newAnnotations: currentTaskStatus?.n_new_annotations ?? 0,
        },
    ];
};
