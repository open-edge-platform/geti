// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    useProjectConfigurationMutation,
    useProjectConfigurationQuery,
} from '../../../../core/configurable-parameters/hooks/use-project-configuration.hook';
import {
    BoolParameter,
    NumberParameter,
} from '../../../../core/configurable-parameters/services/configuration.interface';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { isNotCropTask } from '../../../utils';
import { useAutoTrainingTasksConfig } from './use-tasks-auto-training-config.hook';

export const useActiveLearningConfiguration = (projectIdentifier: ProjectIdentifier, tasks: Task[]) => {
    const { FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS } = useFeatureFlags();
    const { data: projectConfiguration, isPending } = useProjectConfigurationQuery(projectIdentifier, {
        enabled: FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS,
    });

    const projectConfigurationMutation = useProjectConfigurationMutation();
    const notCropTasks = tasks.filter(isNotCropTask);
    const istTaskChain = notCropTasks.length > 1;

    // TODO: check if we can use KeyValueParameter
    // Decide if we can do updateAutoTraining, updateDynamicRequiredAnnotations, and updateRequiredImagesAutoTraining here
    // so we can share the same interface for all updates: taskId?: string, value: boolean | number
    const updateTrainingParameters = ({
        taskId,
    }: {
        taskId?: string;
        key: string;
        value: string | number | boolean;
    }) => {
        projectConfigurationMutation.mutate({
            projectIdentifier,
            queryParameters: istTaskChain ? { taskId } : undefined,
            payload: {},
        });
    };

    const autoTrainingTaskConfigLegacy = useAutoTrainingTasksConfig(projectIdentifier, tasks);

    if (FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS) {
        const autoTrainingTasks = tasks.filter(isNotCropTask).map((task) => {
            const taskProjectConfiguration = projectConfiguration?.taskConfigs.find(
                (taskConfig) => taskConfig.taskId === task.id
            );

            if (taskProjectConfiguration === undefined) {
                return {
                    task,
                    trainingConfig: undefined,
                    dynamicRequiredAnnotationsConfig: undefined,
                    requiredImagesAutoTrainingConfig: undefined,
                };
            }

            return {
                task,
                trainingConfig: taskProjectConfiguration.autoTraining.find(
                    (config) => config.key === 'enable'
                ) as BoolParameter,
                dynamicRequiredAnnotationsConfig: taskProjectConfiguration.autoTraining.find(
                    (config) => config.key === '"enable_dynamic_required_annotations"'
                ) as BoolParameter,
                requiredImagesAutoTrainingConfig: undefined,
            };
        });

        return {
            isPending,
            autoTrainingTasks,
            updateTrainingParameters: () => {},
        };
    }

    return autoTrainingTaskConfigLegacy;
};
