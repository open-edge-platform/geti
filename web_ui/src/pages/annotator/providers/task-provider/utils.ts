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
