// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useConfigParameters } from '../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import { ConfigurableParametersTaskChain } from '../../../../core/configurable-parameters/services/configurable-parameters.interface';
import {
    findAutoTrainingConfig,
    findDynamicRequiredAnnotationsConfig,
    findRequiredImagesAutoTrainingConfig,
} from '../../../../core/configurable-parameters/utils';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { isNotCropTask } from '../../../utils';
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
