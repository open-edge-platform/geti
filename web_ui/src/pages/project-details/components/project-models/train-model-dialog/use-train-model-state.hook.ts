// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { keepPreviousData } from '@tanstack/react-query';
import { isEmpty, isNumber } from 'lodash-es';

import { useConfigParameters } from '../../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import { useTrainingConfigurationQuery } from '../../../../../core/configurable-parameters/hooks/use-training-configuration.hook';
import { TrainingConfiguration } from '../../../../../core/configurable-parameters/services/configuration.interface';
import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { TrainingBodyDTO } from '../../../../../core/models/dtos/train-model.interface';
import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { isActiveModel } from '../../../../../core/models/utils';
import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { Task } from '../../../../../core/projects/task.interface';
import { useTasksWithSupportedAlgorithms } from '../../../../../core/supported-algorithms/hooks/use-tasks-with-supported-algorithms';
import { SupportedAlgorithm } from '../../../../../core/supported-algorithms/supported-algorithms.interface';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { isNotCropTask } from '../../../../../shared/utils';
import { useTotalCreditPrice } from '../../../hooks/use-credits-to-consume.hook';
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

const useTrainingConfiguration = ({
    projectIdentifier,
    selectedTaskId,
    selectedModelTemplateId,
}: {
    projectIdentifier: ProjectIdentifier;
    selectedTaskId: string;
    selectedModelTemplateId: string | null;
}) => {
    const { data } = useTrainingConfigurationQuery(projectIdentifier, {
        modelManifestId: selectedModelTemplateId,
        taskId: selectedTaskId,
    });

    const [trainingConfiguration, setTrainingConfiguration] = useState<TrainingConfiguration | undefined>(data);

    useEffect(() => {
        if (data === undefined) {
            return;
        }

        setTrainingConfiguration(data);
    }, [data]);

    return [trainingConfiguration, setTrainingConfiguration] as const;
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

    const [trainingConfiguration, setTrainingConfiguration] = useTrainingConfiguration({
        projectIdentifier,
        selectedTaskId: selectedTask.id,
        selectedModelTemplateId,
    });

    const { useGetModelConfigParameters } = useConfigParameters(projectIdentifier);
    const { data: configParameters } = useGetModelConfigParameters(
        {
            taskId: selectedTask.id,
            modelTemplateId: selectedModelTemplateId,
            editable: true,
        },
        {
            placeholderData: keepPreviousData,
        }
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

    const handleTrainFromScratchChange = (newTrainFromScratch: boolean): void => {
        setTrainFromScratch(newTrainFromScratch);

        if (newTrainFromScratch === false) {
            setIsReshufflingSubsetsEnabled(false);
        }
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
        changeTrainFromScratch: handleTrainFromScratchChange,
        trainingConfiguration,
        updateTrainingConfiguration: setTrainingConfiguration,
    } as const;
};
