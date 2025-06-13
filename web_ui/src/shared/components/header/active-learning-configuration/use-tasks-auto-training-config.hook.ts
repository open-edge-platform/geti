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
import { UseActiveLearningConfigurationReturnType } from './util';

/**
 * @deprecated
 * This hook is deprecated, please use `useActiveLearningConfiguration` instead.
 * */
export const useAutoTrainingTasksConfig = (
    projectIdentifier: ProjectIdentifier,
    tasks: Task[]
): UseActiveLearningConfigurationReturnType => {
    const { FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS } = useFeatureFlags();

    const { useGetConfigParameters } = useConfigParameters(projectIdentifier);
    const { isPending, data: configParameters } = useGetConfigParameters(!FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS);

    const autoTrainingOptimisticUpdates = useReconfigAutoTraining(projectIdentifier);

    const updateProjectConfiguration = ({
        newConfigParameter,
        onOptimisticUpdate,
    }: Pick<UseReconfigureParams, 'newConfigParameter' | 'onOptimisticUpdate'>) => {
        autoTrainingOptimisticUpdates.mutate({
            configParameters: configParameters ?? [],
            onOptimisticUpdate,
            newConfigParameter,
        });
    };

    const updateAutoTraining = (taskId: string, value: boolean) => {
        if (configParameters === undefined) {
            return;
        }

        const autoTrainingConfig = findAutoTrainingConfig(taskId, configParameters);

        if (autoTrainingConfig === undefined) {
            return;
        }

        updateProjectConfiguration({
            newConfigParameter: {
                ...autoTrainingConfig,
                value,
            },
            onOptimisticUpdate: (config) => {
                const autoTrainingConfigOptimistic = findAutoTrainingConfig(taskId, config);

                if (autoTrainingConfigOptimistic !== undefined) {
                    autoTrainingConfigOptimistic.value = value;
                }

                return config;
            },
        });
    };

    const updateDynamicRequiredAnnotations = (taskId: string, value: boolean) => {
        if (configParameters === undefined) {
            return;
        }

        const dynamicRequiredAnnotationsConfig = findDynamicRequiredAnnotationsConfig(taskId, configParameters);

        if (dynamicRequiredAnnotationsConfig === undefined) {
            return;
        }

        updateProjectConfiguration({
            newConfigParameter: {
                ...dynamicRequiredAnnotationsConfig,
                value,
            },
            onOptimisticUpdate: (config) => {
                const dynamicRequiredAnnotationsConfigOptimistic = findDynamicRequiredAnnotationsConfig(taskId, config);

                if (dynamicRequiredAnnotationsConfigOptimistic !== undefined) {
                    dynamicRequiredAnnotationsConfigOptimistic.value = value;
                }

                return config;
            },
        });
    };

    const updateRequiredImagesAutoTraining = (taskId: string, value: number) => {
        if (configParameters === undefined) {
            return;
        }

        const requiredImagesAutoTrainingConfig = findRequiredImagesAutoTrainingConfig(taskId, configParameters);

        if (requiredImagesAutoTrainingConfig === undefined) {
            return;
        }

        updateProjectConfiguration({
            newConfigParameter: {
                ...requiredImagesAutoTrainingConfig,
                value,
            },
            onOptimisticUpdate: (config) => {
                const requiredImagesAutoTrainingConfigOptimistic = findRequiredImagesAutoTrainingConfig(taskId, config);

                if (requiredImagesAutoTrainingConfigOptimistic !== undefined) {
                    requiredImagesAutoTrainingConfigOptimistic.value = value;
                }

                return config;
            },
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

    return {
        autoTrainingTasks,
        isPending,
        updateAutoTraining,
        updateDynamicRequiredAnnotations,
        updateRequiredImagesAutoTraining,
    };
};
