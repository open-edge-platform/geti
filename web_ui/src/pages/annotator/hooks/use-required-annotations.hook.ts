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
