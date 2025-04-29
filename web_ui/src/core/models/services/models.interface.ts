// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ProjectIdentifier } from '../../projects/core.interface';
import { TaskWithSupportedAlgorithms } from '../../supported-algorithms/supported-algorithms.interface';
import { TrainingBodyDTO } from '../dtos/train-model.interface';
import { ModelGroupIdentifier, ModelIdentifier, ModelsGroups } from '../models.interface';
import { ModelDetails } from '../optimized-models.interface';

export interface ModelsService {
    getModels: (
        projectIdentifier: ProjectIdentifier,
        tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms
    ) => Promise<ModelsGroups[]>;

    getModel: (modelIdentifier: ModelIdentifier) => Promise<ModelDetails>;

    getModelsByArchitecture: (
        modelGroupIdentifier: ModelGroupIdentifier,
        tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms
    ) => Promise<ModelsGroups>;

    trainModel: (projectIdentifier: ProjectIdentifier, body: TrainingBodyDTO) => Promise<void>;

    optimizeModel: (modelIdentifier: ModelIdentifier) => Promise<void>;

    activateModel: (modelGroupIdentifier: ModelGroupIdentifier) => Promise<void>;

    archiveModel: (modelIdentifier: ModelIdentifier) => Promise<void>;
}
