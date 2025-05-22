// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useMemo, useState } from 'react';

import { isNumber } from 'lodash-es';

import { ConfigurableParametersTaskChain } from '../../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { updateSelectedParameter } from '../../../../../../core/configurable-parameters/utils';
import { useFeatureFlags } from '../../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { TrainingBodyDTO } from '../../../../../../core/models/dtos/train-model.interface';
import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { Task } from '../../../../../../core/projects/task.interface';
import { useTasksWithSupportedAlgorithms } from '../../../../../../core/supported-algorithms/hooks/use-tasks-with-supported-algorithms';
import { AnimationDirections } from '../../../../../../shared/animation-parameters/animation-parameters';
import { isNotCropTask } from '../../../../../../shared/utils';
import { useTotalCreditPrice } from '../../../../hooks/use-credits-to-consume.hook';
import { useProject } from '../../../../providers/project-provider/project-provider.component';
import { ModelTemplatesSelection } from '../model-templates-selection/model-templates-selection.component';
import { ModelConfigurationOption } from '../model-templates-selection/utils';
import { TrainConfigurableParameters } from '../train-configurable-parameters/train-configurable-parameters.component';
import { getTrainingBodyDTO } from '../utils';
import { TrainingProcessState, TrainingSteps, UseTrainProcessHandler } from './use-training-state-value.interface';

export const useTrainStateValue = (): UseTrainProcessHandler => {
    const { project, isTaskChainProject } = useProject();
    const { useProjectModelsQuery } = useModels();
    const { data: models } = useProjectModelsQuery();
    const { getCreditPrice } = useTotalCreditPrice();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const tasks = project.tasks.filter(isNotCropTask);
    const [task] = tasks;
    const { tasksWithSupportedAlgorithms } = useTasksWithSupportedAlgorithms();
    const [selectedTask, setSelectedTask] = useState<Task>(task);

    const [currentStep, setCurrentStep] = useState<TrainingSteps>(TrainingSteps.MODEL_TEMPLATE_SELECTION);
    const [selectedModelTemplateId, setSelectedModelTemplateId] = useState<string | null>(null);
    const [modelConfigurationOption, setModelConfigurationOption] = useState<ModelConfigurationOption>(
        ModelConfigurationOption.LATEST_CONFIGURATION
    );

    const isManualConfigurationSelected = modelConfigurationOption === ModelConfigurationOption.MANUAL_CONFIGURATION;

    const [configParameters, setConfigParameters] = useState<ConfigurableParametersTaskChain | undefined>(undefined);

    const [trainFromScratch, setTrainFromScratch] = useState<boolean>(false);
    const [isReshufflingSubsetsEnabled, setIsReshufflingSubsetsEnabled] = useState<boolean>(false);
    const [animationDirection, setAnimationDirection] = useState<number>(AnimationDirections.MOVE_LEFT);

    const updateParameter = useCallback(<T extends string | boolean | number>(id: string, value: T): void => {
        const ids = id.split('::');
        ids.length > 2 &&
            setConfigParameters((prevConfigParameters) => {
                if (prevConfigParameters) {
                    return updateSelectedParameter([prevConfigParameters], id, ids, value)[0];
                }
                return prevConfigParameters;
            });
    }, []);

    const handleSelectedTemplateId = (modelTemplateId: string | null): void => {
        if (modelTemplateId === selectedModelTemplateId) {
            return;
        }

        setSelectedModelTemplateId(modelTemplateId);

        // reject old configurable parameters when modelTemplateId has changed
        setConfigParameters(undefined);
    };

    const handleChangeTrainFromScratch = (isTrainFromScratchEnabled: boolean): void => {
        setTrainFromScratch(isTrainFromScratchEnabled);

        if (!isTrainFromScratchEnabled && isReshufflingSubsetsEnabled) {
            setIsReshufflingSubsetsEnabled(false);
        }
    };

    const getStep = useCallback(
        (step: TrainingSteps): TrainingProcessState => {
            switch (step) {
                case TrainingSteps.MODEL_TEMPLATE_SELECTION: {
                    return {
                        key: TrainingSteps.MODEL_TEMPLATE_SELECTION,
                        description: 'Select template',
                        prev: null,
                        next: isManualConfigurationSelected ? TrainingSteps.CONFIGURABLE_PARAMETERS : null,
                    };
                }
                case TrainingSteps.CONFIGURABLE_PARAMETERS: {
                    return {
                        key: TrainingSteps.CONFIGURABLE_PARAMETERS,
                        description: 'Configure parameters',
                        stepNumber: 2,
                        prev: TrainingSteps.MODEL_TEMPLATE_SELECTION,
                        next: null,
                    };
                }
                default:
                    throw new Error(`Training step: ${step} is not supported`);
            }
        },
        [isManualConfigurationSelected]
    );

    const renderCurrentStep = (step: TrainingSteps): JSX.Element => {
        switch (step) {
            case TrainingSteps.MODEL_TEMPLATE_SELECTION: {
                return (
                    <ModelTemplatesSelection
                        models={models}
                        selectedTask={selectedTask}
                        setSelectedTask={setSelectedTask}
                        animationDirection={animationDirection}
                        selectedModelTemplateId={selectedModelTemplateId}
                        handleSelectedTemplateId={handleSelectedTemplateId}
                        modelConfigurationOption={modelConfigurationOption}
                        setModelConfigurationOption={setModelConfigurationOption}
                        tasksWithSupportedAlgorithms={tasksWithSupportedAlgorithms}
                    />
                );
            }
            case TrainingSteps.CONFIGURABLE_PARAMETERS: {
                return selectedModelTemplateId ? (
                    <TrainConfigurableParameters
                        configParameters={configParameters}
                        setConfigParameters={setConfigParameters}
                        trainFromScratch={trainFromScratch}
                        setTrainFromScratch={handleChangeTrainFromScratch}
                        modelTemplateId={selectedModelTemplateId}
                        updateParameter={updateParameter}
                        taskId={selectedTask.id}
                        animationDirection={animationDirection}
                        isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                        onChangeReshuffleSubsets={setIsReshufflingSubsetsEnabled}
                    />
                ) : (
                    <></>
                );
            }
            default:
                throw new Error(`Training step: ${step} is not supported`);
        }
    };

    const stepConfig = useMemo(() => getStep(currentStep), [currentStep, getStep]);

    const { next, prev } = stepConfig;

    const showNextButton = next !== null;
    const showBackButton = prev !== null;

    const nextAction = (): void => {
        if (next !== null) {
            setAnimationDirection(() => AnimationDirections.MOVE_RIGHT);
            setCurrentStep(next);
        }
    };

    const prevAction = (): void => {
        if (prev !== null) {
            setAnimationDirection(() => AnimationDirections.MOVE_LEFT);
            setCurrentStep(prev);
        }
    };

    const handleDefaultStateOnClose = (): void => {
        isTaskChainProject && setSelectedTask(task);
        setSelectedModelTemplateId(null);
        setModelConfigurationOption(ModelConfigurationOption.LATEST_CONFIGURATION);

        setTrainFromScratch(false);
        setIsReshufflingSubsetsEnabled(false);

        if (configParameters) {
            setConfigParameters(undefined);
        }

        currentStep !== TrainingSteps.MODEL_TEMPLATE_SELECTION &&
            setCurrentStep(TrainingSteps.MODEL_TEMPLATE_SELECTION);

        animationDirection !== AnimationDirections.MOVE_LEFT && setAnimationDirection(AnimationDirections.MOVE_LEFT);
    };

    const handleTrainingBodyDTO = (): TrainingBodyDTO => {
        const configParam = isManualConfigurationSelected ? configParameters : undefined;
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

    return {
        nextAction,
        prevAction,
        stepConfig,
        showBackButton,
        showNextButton,
        selectedTask,
        handleChangeSelectedTask: setSelectedTask,
        renderCurrentStep,
        handleDefaultStateOnClose,
        tasks,
        trainingBodyDTO: handleTrainingBodyDTO(),
    };
};
