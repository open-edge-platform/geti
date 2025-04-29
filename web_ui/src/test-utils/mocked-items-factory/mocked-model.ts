// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';

import { ModelFormat } from '../../core/models/dtos/model-details.interface';
import { ModelGroupsAlgorithmDetails, ModelsGroups } from '../../core/models/models.interface';
import { OptimizedModel, TrainedModel } from '../../core/models/optimized-models.interface';
import { PerformanceType } from '../../core/projects/task.interface';
import {
    LifecycleStage,
    PerformanceCategory,
} from '../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { ModelVersion } from '../../pages/project-details/components/project-models/models-container/model-card/model-card.interface';

export const getMockedModelVersion = (modelVersion?: Partial<ModelVersion>): ModelVersion => {
    return {
        version: 1,
        id: 'model-id',
        groupId: 'architecture-id',
        creationDate: dayjs().toString(),
        performance: {
            score: 0.5,
            type: PerformanceType.DEFAULT,
        },
        isLabelSchemaUpToDate: true,
        isActiveModel: true,
        groupName: 'SSD',
        templateName: 'Speed',
        modelSize: 1000,
        ...modelVersion,
    };
};

export const getMockedModelsGroup = (modelsGroup?: Partial<ModelsGroups>): ModelsGroups => {
    return {
        modelTemplateId: 'Custom_Object_Detection_Gen3_SSD',
        modelVersions: [getMockedModelVersion()],
        taskId: 'task-id',
        modelSummary: 'SSD summary',
        modelTemplateName: 'Speed',
        groupId: 'architecture-id',
        groupName: 'SSD group',
        lifecycleStage: LifecycleStage.ACTIVE,
        ...modelsGroup,
    };
};

export const getMockedModelsGroupAlgorithmDetails = (
    modelsGroup?: Partial<ModelGroupsAlgorithmDetails>
): ModelGroupsAlgorithmDetails => {
    return {
        modelTemplateId: 'Custom_Object_Detection_Gen3_SSD',
        modelVersions: [getMockedModelVersion()],
        taskId: 'task-id',
        modelSummary: 'SSD summary',
        modelTemplateName: 'Speed',
        groupId: 'architecture-id',
        groupName: 'SSD group',
        isDefaultAlgorithm: false,
        lifecycleStage: LifecycleStage.ACTIVE,
        performanceCategory: PerformanceCategory.OTHER,
        complexity: 100,
        ...modelsGroup,
    };
};

export const getMockedOptimizedModel = (optimizedModel: Partial<OptimizedModel> = {}): OptimizedModel => {
    return {
        id: '123',
        version: 1,
        precision: ['FP32'],
        configurations: [],
        modelName: 'ATSS OpenVINO',
        modelStatus: 'SUCCESS',
        creationDate: '2023-03-22T08:39:35.532000+00:00',
        previousRevisionId: '641abec79cc05824cf4a9961',
        optimizationMethods: [],
        optimizationObjectives: {},
        previousTrainedRevisionId: '641abec79cc05824cf4a9961',
        optimizationType: 'MO',
        accuracy: 0.4,
        modelSize: '9.97 MB',
        labels: [],
        hasExplainableAI: false,
        modelFormat: ModelFormat.OpenVINO,
        license: 'Apache 2.0',
        lifecycleStage: LifecycleStage.ACTIVE,
        ...optimizedModel,
    };
};

export const getMockedTrainedModel = (trainedModel: Partial<TrainedModel> = {}): TrainedModel => {
    return {
        modelName: 'YoloV4 pytorch',
        modelSize: '23222',
        totalDiskSize: '10 MB',
        precision: ['FP32'],
        accuracy: 0.484,
        architecture: 'U-net',
        previousRevisionId: '1',
        previousTrainedRevisionId: '12',
        version: 1,
        id: '2',
        labels: [],
        creationDate: dayjs().toString(),
        isLabelSchemaUpToDate: true,
        numberOfFrames: 1,
        numberOfImages: 2,
        numberOfSamples: 3,
        license: 'Apache 2.0',
        lifecycleStage: LifecycleStage.ACTIVE,
        ...trainedModel,
    };
};

export const getMockedModelGroups = (modelsGroups: Partial<ModelsGroups> = {}): ModelsGroups => {
    return {
        modelTemplateId: 'Custom_Object_Detection_Gen3_SSD',
        modelVersions: [getMockedModelVersion()],
        taskId: 'task-id',
        modelSummary: 'SSD summary',
        modelTemplateName: 'Speed',
        groupId: 'architecture-id',
        groupName: 'SSD group',
        lifecycleStage: LifecycleStage.ACTIVE,
        ...modelsGroups,
    };
};
