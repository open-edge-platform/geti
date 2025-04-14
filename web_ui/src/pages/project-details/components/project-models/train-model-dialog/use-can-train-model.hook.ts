// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
