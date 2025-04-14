// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';

import { getMockedOptimizedModel, getMockedTrainedModel } from '../../../test-utils/mocked-items-factory/mocked-model';
import { LifecycleStage } from '../../supported-algorithms/dtos/supported-algorithms.interface';
import { mockedSupportedAlgorithms } from '../../supported-algorithms/services/test-utils';
import { ModelFormat } from '../dtos/model-details.interface';
import { ModelDTO, ModelsDTO } from '../dtos/models.interface';
import { ModelsGroups } from '../models.interface';
import { OptimizedModel, TrainedModel } from '../optimized-models.interface';
import { getModelsEntity } from './utils';

const mockedModelsYoloDTO: ModelDTO[] = [
    {
        id: '3',
        name: 'YoloV4',
        size: 120000,
        performance: { score: 0.9 },
        active_model: false,
        creation_date: dayjs().subtract(1, 'day').toString(),
        version: 1,
        label_schema_in_sync: true,
        total_disk_size: 10,
        lifecycle_stage: LifecycleStage.ACTIVE,
    },
    {
        id: '4',
        name: 'YoloV4',
        size: 140000,
        performance: { score: 0.95 },
        active_model: false,
        creation_date: dayjs().toString(),
        version: 2,
        label_schema_in_sync: true,
        total_disk_size: 10,
        lifecycle_stage: LifecycleStage.ACTIVE,
    },
];

const mockedModelsATSSDTO: ModelDTO[] = [
    {
        id: '1',
        name: 'ATSS',
        performance: { score: 0.24 },
        size: 220000,
        active_model: false,
        creation_date: dayjs().subtract(1, 'd').toString(),
        version: 1,
        label_schema_in_sync: true,
        total_disk_size: 10,
        lifecycle_stage: LifecycleStage.ACTIVE,
    },
    {
        id: '2',
        name: 'ATSS',
        performance: { score: 0.71 },
        size: 230000,
        active_model: true,
        creation_date: dayjs().toString(),
        version: 2,
        label_schema_in_sync: true,
        total_disk_size: 10,
        lifecycle_stage: LifecycleStage.ACTIVE,
    },
];

export const mockedArchitectureModelsDTO: ModelsDTO[] = [
    {
        id: 'model-group-1-id',
        name: 'YoloV4',
        model_template_id: 'Custom_Object_Detection_Gen3_SSD',
        task_id: '1234',
        models: mockedModelsYoloDTO,
        lifecycle_stage: LifecycleStage.ACTIVE,
    },
    {
        id: 'model-group-2-id',
        name: 'ATSS',
        model_template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR',
        task_id: '1235',
        models: mockedModelsATSSDTO,
        lifecycle_stage: LifecycleStage.ACTIVE,
    },
];

export const mockedArchitectureModels: ModelsGroups[] = getModelsEntity(mockedArchitectureModelsDTO, {
    [mockedArchitectureModelsDTO[0].task_id]: mockedSupportedAlgorithms,
    [mockedArchitectureModelsDTO[1].task_id]: mockedSupportedAlgorithms,
});

export const mockedTrainedModel: TrainedModel = getMockedTrainedModel({
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
});

export const mockedOptimizedModels: OptimizedModel[] = [
    getMockedOptimizedModel({
        id: '1',
        modelSize: '23200',
        creationDate: dayjs().toString(),
        optimizationType: 'MO',
        previousTrainedRevisionId: '1',
        previousRevisionId: '2',
        optimizationObjectives: {},
        optimizationMethods: [],
        modelName: 'YoloV4 pytorch',
        precision: ['FP16'],
        accuracy: 0.484,
        modelStatus: 'SUCCESS',
        labels: [],
        version: 1,
        configurations: [],
        hasExplainableAI: false,
        modelFormat: ModelFormat.OpenVINO,
        lifecycleStage: LifecycleStage.ACTIVE,
    }),
    getMockedOptimizedModel({
        id: '2',
        modelSize: '2321321',
        creationDate: dayjs().toString(),
        optimizationType: 'MO',
        previousTrainedRevisionId: '3',
        previousRevisionId: '4',
        optimizationObjectives: {},
        optimizationMethods: [],
        modelName: 'YoloV4 pytorch',
        precision: ['INT8'],
        accuracy: 0.344,
        modelStatus: 'SUCCESS',
        labels: [],
        version: 1,
        configurations: [],
        hasExplainableAI: false,
        modelFormat: ModelFormat.OpenVINO,
        lifecycleStage: LifecycleStage.ACTIVE,
    }),
    getMockedOptimizedModel({
        id: '3',
        modelSize: '23.20 MB',
        creationDate: dayjs().toString(),
        optimizationType: 'MO',
        previousTrainedRevisionId: '1',
        previousRevisionId: '2',
        optimizationObjectives: {},
        optimizationMethods: [],
        modelName: 'YoloV4 pytorch',
        precision: ['FP32'],
        accuracy: 0.484,
        modelStatus: 'SUCCESS',
        labels: [],
        version: 1,
        configurations: [],
        hasExplainableAI: false,
        modelFormat: ModelFormat.OpenVINO,
        lifecycleStage: LifecycleStage.ACTIVE,
    }),
];
