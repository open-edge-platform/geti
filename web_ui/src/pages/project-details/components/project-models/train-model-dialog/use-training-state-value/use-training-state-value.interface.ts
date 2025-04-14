// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TrainingBodyDTO } from '../../../../../../core/models/dtos/train-model.interface';
import { Task } from '../../../../../../core/projects/task.interface';

export enum TrainingSteps {
    MODEL_TEMPLATE_SELECTION = 'model-template-selection',
    CONFIGURABLE_PARAMETERS = 'configurable-parameters',
}

export interface TrainingProcessState {
    key: TrainingSteps;
    description: string;
    stepNumber?: number;
    prev: TrainingSteps | null;
    next: TrainingSteps | null;
}

export interface UseTrainProcessHandler {
    stepConfig: TrainingProcessState;
    selectedTask: Task;
    showNextButton: boolean;
    showBackButton: boolean;
    nextAction: () => void;
    prevAction: () => void;
    trainingBodyDTO: TrainingBodyDTO;
    handleDefaultStateOnClose: () => void;
    renderCurrentStep: (step: TrainingSteps) => JSX.Element;
    handleChangeSelectedTask: (task: Task) => void;
    tasks: Task[];
}
