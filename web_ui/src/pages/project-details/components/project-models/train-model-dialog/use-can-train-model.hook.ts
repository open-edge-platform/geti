// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { useProjectStatus } from '../../../../../core/projects/hooks/use-project-status.hook';
import { Task } from '../../../../../core/projects/task.interface';
import { hasEqualId } from '../../../../../shared/utils';

const MIN_NUMBER_OF_REQUIRED_ANNOTATIONS = 3;

export const useCanTrainModel = (
    projectIdentifier: ProjectIdentifier,
    task: Task
):
    | { canTrainModel: true; numberOfRequiredAnnotations: undefined }
    | { canTrainModel: false; numberOfRequiredAnnotations: number } => {
    const { data } = useProjectStatus(projectIdentifier);

    const selectedTask = data?.tasks.find(hasEqualId(task.id));

    const newAnnotations = selectedTask?.n_new_annotations ?? 0;
    const requiredAnnotations = MIN_NUMBER_OF_REQUIRED_ANNOTATIONS - newAnnotations;
    const canTrainModel = selectedTask?.ready_to_train || requiredAnnotations === 0;

    if (canTrainModel) {
        return {
            canTrainModel: true,
            numberOfRequiredAnnotations: undefined,
        };
    }

    return {
        canTrainModel: false,
        numberOfRequiredAnnotations: Math.min(requiredAnnotations, MIN_NUMBER_OF_REQUIRED_ANNOTATIONS),
    };
};
