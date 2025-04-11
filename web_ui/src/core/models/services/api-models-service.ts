// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ProjectIdentifier } from '../../projects/core.interface';
import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { TaskWithSupportedAlgorithms } from '../../supported-algorithms/supported-algorithms.interface';
import { ModelDetailsDTO } from '../dtos/model-details.interface';
import { ModelGroupsDTO, ModelsDTO } from '../dtos/models.interface';
import { TrainingBodyDTO } from '../dtos/train-model.interface';
import { ModelGroupIdentifier, ModelIdentifier, ModelsGroups } from '../models.interface';
import { ModelDetails } from '../optimized-models.interface';
import { ModelsService } from './models.interface';
import { checkModelIntegrity, getModelEntity, getModelsEntity } from './utils';

export const createApiModelsService: CreateApiService<ModelsService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getModels: ModelsService['getModels'] = async (
        projectIdentifier: ProjectIdentifier,
        tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms
    ): Promise<ModelsGroups[]> => {
        const { data } = await instance.get<ModelGroupsDTO>(router.MODELS(projectIdentifier));

        const modelGroups = getModelsEntity(data.model_groups, tasksWithSupportedAlgorithms);

        const validModelGroups = modelGroups.filter(checkModelIntegrity);

        return validModelGroups;
    };

    const getModelsByArchitecture: ModelsService['getModelsByArchitecture'] = async (
        modelGroupIdentifier: ModelGroupIdentifier,
        tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms
    ): Promise<ModelsGroups> => {
        const { data } = await instance.get<ModelsDTO>(router.MODEL_GROUPS(modelGroupIdentifier));

        return getModelsEntity([data], tasksWithSupportedAlgorithms)[0];
    };

    const getModel: ModelsService['getModel'] = async (modelIdentifier: ModelIdentifier): Promise<ModelDetails> => {
        const { data } = await instance.get<ModelDetailsDTO>(router.MODEL(modelIdentifier));

        return getModelEntity(data);
    };

    const trainModel: ModelsService['trainModel'] = async (
        projectIdentifier: ProjectIdentifier,
        body: TrainingBodyDTO
    ): Promise<void> => {
        await instance.post(router.MANUAL_TRAIN_MODEL(projectIdentifier), body);
    };

    const optimizeModel: ModelsService['optimizeModel'] = async (modelIdentifier: ModelIdentifier): Promise<void> => {
        await instance.post(router.OPTIMIZE_MODEL(modelIdentifier));
    };

    const activateModel: ModelsService['activateModel'] = async (
        modelGroupIdentifier: ModelGroupIdentifier
    ): Promise<void> => {
        await instance.post(router.ACTIVATE_MODEL(modelGroupIdentifier));
    };

    const archiveModel: ModelsService['archiveModel'] = async (modelIdentifier: ModelIdentifier): Promise<void> => {
        await instance.post(router.ARCHIVE_MODEL(modelIdentifier));
    };

    return {
        getModels,
        getModel,
        getModelsByArchitecture,
        trainModel,
        optimizeModel,
        activateModel,
        archiveModel,
    };
};
