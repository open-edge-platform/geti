// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ProjectIdentifier } from '../../../core/projects/core.interface';
import { ProjectProps } from '../../../core/projects/project.interface';
import { useAutoTrainingTasksConfig } from '../../../shared/components/header/active-learning-configuration/use-tasks-auto-training-config.hook';

export const useIsAutoTrainingOn = ({
    project,
    projectIdentifier,
}: {
    project: ProjectProps;
    projectIdentifier: ProjectIdentifier;
}) => {
    const { autoTrainingTasks, isPending } = useAutoTrainingTasksConfig(projectIdentifier, project.tasks);

    return !isPending && autoTrainingTasks.some(({ trainingConfig }) => trainingConfig?.value === true);
};
