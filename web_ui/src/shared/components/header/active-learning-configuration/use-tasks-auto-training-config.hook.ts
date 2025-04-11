// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useConfigParameters } from '../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import {
    findAutoTrainingConfig,
    findDynamicRequiredAnnotationsConfig,
    findRequiredImagesAutoTrainingConfig,
} from '../../../../core/configurable-parameters/utils';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { isNotCropTask } from '../../../utils';
import { ConfigurableParametersTaskChain } from '../../configurable-parameters/configurable-parameters.interface';
import { AutoTrainingTask } from './util';

export const useAutoTrainingTasksConfig = (
    projectIdentifier: ProjectIdentifier,
    tasks: Task[]
): {
    isLoading: boolean;
    autoTrainingTasks: AutoTrainingTask[];
    configParameters?: ConfigurableParametersTaskChain[];
} => {
    const { useGetConfigParameters } = useConfigParameters(projectIdentifier);
    const { isPending, data: configParameters } = useGetConfigParameters(true);

    const autoTrainingTasks = tasks.filter(isNotCropTask).map(
        (task): AutoTrainingTask => ({
            task,
            trainingConfig:
                configParameters === undefined ? undefined : findAutoTrainingConfig(task.id, configParameters),
            dynamicRequiredAnnotationsConfig:
                configParameters === undefined
                    ? undefined
                    : findDynamicRequiredAnnotationsConfig(task.id, configParameters),
            requiredImagesAutoTrainingConfig:
                configParameters === undefined
                    ? undefined
                    : findRequiredImagesAutoTrainingConfig(task.id, configParameters),
        })
    );

    return { autoTrainingTasks, isLoading: isPending, configParameters };
};
