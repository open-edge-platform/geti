// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    ProjectStatusRequiredAnnotationsDetailEntryDTO,
    ProjectStatusTaskDTO,
} from '../../../../core/projects/dtos/status.interface';
import { RequiredAnnotationsDetailsEntry } from '../../../../core/projects/project-status.interface';
import { Task } from '../../../../core/projects/task.interface';

export const getTaskRequiredAnnotationsDetails = (
    projectTask?: ProjectStatusTaskDTO,
    _selectedTask?: Task | null
): RequiredAnnotationsDetailsEntry[] => {
    if (!projectTask) return [];

    const requiredAnnotationsDetails = projectTask.required_annotations.details;

    return requiredAnnotationsDetails.map(
        (requiredAnnotationsDetail: ProjectStatusRequiredAnnotationsDetailEntryDTO) => ({
            id: requiredAnnotationsDetail.id,
            name: requiredAnnotationsDetail.label_name,
            color: requiredAnnotationsDetail.label_color,
            value: requiredAnnotationsDetail.value,
        })
    );
};
