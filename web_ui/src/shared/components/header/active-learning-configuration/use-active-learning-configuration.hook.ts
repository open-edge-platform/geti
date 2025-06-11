// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    useProjectConfigurationMutation,
    useProjectConfigurationQuery,
} from '../../../../core/configurable-parameters/hooks/use-project-configuration.hook';
import {
    BoolParameter,
    ProjectConfigurationUploadPayload,
} from '../../../../core/configurable-parameters/services/configuration.interface';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { isNotCropTask } from '../../../utils';
import { useAutoTrainingTasksConfig } from './use-tasks-auto-training-config.hook';
import { UseActiveLearningConfigurationReturnType } from './util';

export const useActiveLearningConfiguration = (
    projectIdentifier: ProjectIdentifier,
    tasks: Task[]
): UseActiveLearningConfigurationReturnType => {
    const { FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS } = useFeatureFlags();
    const { data: projectConfiguration, isPending } = useProjectConfigurationQuery(projectIdentifier, {
        enabled: FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS,
    });

    const projectConfigurationMutation = useProjectConfigurationMutation();
    const notCropTasks = tasks.filter(isNotCropTask);
    const istTaskChain = notCropTasks.length > 1;

    const updateProjectConfiguration = ({
        taskId,
        payload,
    }: {
        taskId?: string;
        payload: ProjectConfigurationUploadPayload;
    }) => {
        projectConfigurationMutation.mutate({
            projectIdentifier,
            payload,
            queryParameters: istTaskChain ? { taskId } : undefined,
        });
    };

    const updateAutoTraining = (taskId: string, value: boolean) => {
        updateProjectConfiguration({
            taskId,
            payload: {
                autoTraining: [
                    {
                        key: 'enable',
                        value,
                    },
                ],
            },
        });
    };

    const updateDynamicRequiredAnnotations = (taskId: string, value: boolean) => {
        updateProjectConfiguration({
            taskId,
            payload: {
                autoTraining: [
                    {
                        key: 'enable_dynamic_required_annotations',
                        value,
                    },
                ],
            },
        });
    };

    const updateRequiredImagesAutoTraining = (taskId: string, value: number) => {
        updateProjectConfiguration({
            taskId,
            payload: {
                autoTraining: [
                    {
                        key: 'required_images_auto_training',
                        value,
                    },
                ],
            },
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
            updateAutoTraining,
            updateDynamicRequiredAnnotations,
            updateRequiredImagesAutoTraining,
        };
    }

    return autoTrainingTaskConfigLegacy;
};
