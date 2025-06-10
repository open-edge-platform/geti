// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useConfigParameters } from '../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import {
    useReconfigAutoTraining,
    UseReconfigureParams,
} from '../../../../core/configurable-parameters/hooks/use-reconfig-auto-training.hook';
import {
    findAutoTrainingConfig,
    findDynamicRequiredAnnotationsConfig,
    findRequiredImagesAutoTrainingConfig,
} from '../../../../core/configurable-parameters/utils';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { isNotCropTask } from '../../../utils';
import { AutoTrainingTask } from './util';

export const useAutoTrainingTasksConfig = (
    projectIdentifier: ProjectIdentifier,
    tasks: Task[]
): {
    isPending: boolean;
    autoTrainingTasks: AutoTrainingTask[];
    updateTrainingParameters: ({
        newConfigParameter,
        onOptimisticUpdate,
    }: Pick<UseReconfigureParams, 'newConfigParameter' | 'onOptimisticUpdate'>) => void;
} => {
    const { FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS } = useFeatureFlags();

    const { useGetConfigParameters } = useConfigParameters(projectIdentifier);
    const { isPending, data: configParameters } = useGetConfigParameters(!FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS);

    const autoTrainingOptimisticUpdates = useReconfigAutoTraining(projectIdentifier);

    const updateTrainingParameters = ({
        newConfigParameter,
        onOptimisticUpdate,
    }: Pick<UseReconfigureParams, 'newConfigParameter' | 'onOptimisticUpdate'>) => {
        autoTrainingOptimisticUpdates.mutate({
            configParameters: configParameters ?? [],
            onOptimisticUpdate,
            newConfigParameter,
        });
    };

    const autoTrainingTasks = tasks.filter(isNotCropTask).map((task) => ({
        task,
        trainingConfig: configParameters === undefined ? undefined : findAutoTrainingConfig(task.id, configParameters),
        dynamicRequiredAnnotationsConfig:
            configParameters === undefined
                ? undefined
                : findDynamicRequiredAnnotationsConfig(task.id, configParameters),
        requiredImagesAutoTrainingConfig:
            configParameters === undefined
                ? undefined
                : findRequiredImagesAutoTrainingConfig(task.id, configParameters),
    }));

    return { autoTrainingTasks, isPending, updateTrainingParameters };
};
