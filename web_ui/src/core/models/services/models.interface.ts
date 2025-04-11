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
