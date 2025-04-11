// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
    const { autoTrainingTasks, isLoading } = useAutoTrainingTasksConfig(projectIdentifier, project.tasks);

    return !isLoading && autoTrainingTasks.some(({ trainingConfig }) => trainingConfig?.value === true);
};
