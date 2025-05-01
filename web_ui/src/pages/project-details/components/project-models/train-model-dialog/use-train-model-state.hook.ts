// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { isNotCropTask } from '@shared/utils';
import isEmpty from 'lodash/isEmpty';
import isNumber from 'lodash/isNumber';

import { useConfigParameters } from '../../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { TrainingBodyDTO } from '../../../../../core/models/dtos/train-model.interface';
import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { isActiveModel } from '../../../../../core/models/utils';
import { Task } from '../../../../../core/projects/task.interface';
import { SupportedAlgorithm } from '../../../../../core/supported-algorithms/supported-algorithms.interface';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { useTotalCreditPrice } from '../../../hooks/use-credits-to-consume.hook';
import { useTasksWithSupportedAlgorithms } from '../../../hooks/use-tasks-with-supported-algorithms';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { getTrainingBodyDTO } from '../legacy-train-model-dialog/utils';

enum TrainModelMode {
    BASIC = 'Basic',
    ADVANCED_SETTINGS = 'Advanced settings',
}

const getActiveModelTemplateId = (
    modelsGroups: ModelsGroups[] | undefined,
    algorithms: SupportedAlgorithm[],
    taskId: string
): string | null => {
    if (isEmpty(modelsGroups)) {
        return algorithms.find((algorithm) => algorithm.isDefaultAlgorithm)?.modelTemplateId ?? null;
    }

    return (
        modelsGroups?.find((modelGroup) => modelGroup.taskId === taskId && modelGroup.modelVersions.some(isActiveModel))
            ?.modelTemplateId ?? null
    );
};

export const useTrainModelState = () => {
    const [mode, setMode] = useState<TrainModelMode>(TrainModelMode.BASIC);

    const projectIdentifier = useProjectIdentifier();
    const { project, isTaskChainProject } = useProject();
    const { useProjectModelsQuery } = useModels();
    const { data: models } = useProjectModelsQuery();
    const { getCreditPrice } = useTotalCreditPrice();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const tasks = project.tasks.filter(isNotCropTask);
    const [task] = tasks;
    const { tasksWithSupportedAlgorithms } = useTasksWithSupportedAlgorithms();
    const [selectedTask, setSelectedTask] = useState<Task>(task);
    const algorithms = tasksWithSupportedAlgorithms[selectedTask.id] ?? [];

    const activeModelTemplateId = getActiveModelTemplateId(models, algorithms, selectedTask.id);
    const [selectedModelTemplateId, setSelectedModelTemplateId] = useState<string | null>(activeModelTemplateId);

    const isBasicMode = mode === TrainModelMode.BASIC;
    const isAdvancedSettingsMode = mode === TrainModelMode.ADVANCED_SETTINGS;

    const { useGetModelConfigParameters } = useConfigParameters(projectIdentifier);
    const { data: configParameters } = useGetModelConfigParameters(
        {
            taskId: selectedTask.id,
            modelTemplateId: selectedModelTemplateId,
            editable: true,
        },
        { enabled: isAdvancedSettingsMode }
    );

    const [isReshufflingSubsetsEnabled, setIsReshufflingSubsetsEnabled] = useState<boolean>(false);
    const [trainFromScratch, setTrainFromScratch] = useState<boolean>(false);

    if (selectedModelTemplateId === null) {
        setSelectedModelTemplateId(activeModelTemplateId);
    }

    const openAdvancedSettingsMode = (): void => {
        setMode(TrainModelMode.ADVANCED_SETTINGS);
    };

    const constructTrainingBodyDTO = (): TrainingBodyDTO => {
        const configParam = undefined;

        const { totalMedias } = getCreditPrice(selectedTask.id);
        const maxTrainingDatasetSize = FEATURE_FLAG_CREDIT_SYSTEM && isNumber(totalMedias) ? totalMedias : undefined;

        return getTrainingBodyDTO({
            modelTemplateId: selectedModelTemplateId ?? '',
            configParameters: configParam,
            taskId: selectedTask.id,
            trainFromScratch,
            isReshufflingSubsetsEnabled,
            maxTrainingDatasetSize,
        });
    };

    const changeTask = (newTask: Task): void => {
        setSelectedTask(newTask);
        setSelectedModelTemplateId(getActiveModelTemplateId(models, algorithms, newTask.id));
    };

    return {
        isBasicMode,
        openAdvancedSettingsMode,
        selectedTask,
        tasks,
        activeModelTemplateId,
        selectedModelTemplateId,
        algorithms,
        changeTask,
        changeSelectedTemplateId: setSelectedModelTemplateId,
        trainingBodyDTO: constructTrainingBodyDTO(),
        isTaskChainProject,
        isReshufflingSubsetsEnabled,
        changeReshufflingSubsetsEnabled: setIsReshufflingSubsetsEnabled,
        configParameters,
        trainFromScratch,
        changeTrainFromScratch: setTrainFromScratch,
    } as const;
};
