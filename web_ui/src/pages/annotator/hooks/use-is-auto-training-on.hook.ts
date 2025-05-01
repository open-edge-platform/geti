// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useAutoTrainingTasksConfig } from '@shared/components/header/active-learning-configuration/use-tasks-auto-training-config.hook';

import { ProjectIdentifier } from '../../../core/projects/core.interface';
import { ProjectProps } from '../../../core/projects/project.interface';

export const useIsAutoTrainingOn = ({
    project,
    projectIdentifier,
}: {
    project: ProjectProps;
    projectIdentifier: ProjectIdentifier;
}) => {
    const { autoTrainingTasks, isLoading } = useAutoTrainingTasksConfig(projectIdentifier, project.tasks);

    return !isLoading && autoTrainingTasks.some(({ trainingConfig }) => trainingConfig?.value === true);
};
