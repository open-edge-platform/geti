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
