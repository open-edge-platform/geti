// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TrainingDatasetInfo } from '../datasets/services/training-dataset.interface';
import { Label } from '../labels/label.interface';
import { ModelDetailsDTO, ModelFormat, OptimizedModelsDTO, TrainedModelDTO } from './dtos/model-details.interface';
import { ModelDTO } from './dtos/models.interface';

export const BASELINE_MODEL = 'Baseline Model';
export const OPENVINO_BASE_MODEL = 'OpenVINO Base Model';
export const POT_OPTIMIZATION = 'Post training optimization';
export const ONNX_MODEL = 'Open Neural Network Exchange';
export const PYTORCH_MODEL = 'Pytorch model';

type ModelOmitFields =
    | 'name'
    | 'previous_revision_id'
    | 'previous_trained_revision_id'
    | 'creation_date'
    | 'score'
    | 'model_status'
    | 'optimization_capabilities'
    | 'size'
    | 'training_dataset_info'
    | 'performance'
    | 'label_schema_in_sync'
    | 'total_disk_size'
    | 'lifecycle_stage';

type OptimizedModelOmitFields =
    | 'architecture'
    | 'optimizationCapabilities'
    | 'numberOfFrames'
    | 'numberOfImages'
    | 'numberOfSamples'
    | 'isLabelSchemaUpToDate'
    | 'totalDiskSize';

export interface TrainedModel extends Omit<TrainedModelDTO, ModelOmitFields> {
    modelName: ModelDetailsDTO['name'];
    modelSize: string;
    totalDiskSize: string;
    creationDate: ModelDetailsDTO['creation_date'];
    accuracy: number | null;
    version: number;
    isLabelSchemaUpToDate: ModelDetailsDTO['label_schema_in_sync'];
    previousRevisionId: ModelDetailsDTO['previous_revision_id'];
    previousTrainedRevisionId: ModelDetailsDTO['previous_trained_revision_id'];
    numberOfFrames: ModelDetailsDTO['training_dataset_info']['n_frames'];
    numberOfImages: ModelDetailsDTO['training_dataset_info']['n_images'];
    numberOfSamples: ModelDetailsDTO['training_dataset_info']['n_samples'];
    license: string;
    lifecycleStage: ModelDTO['lifecycle_stage'];
}

export type OptimizationTypes = 'MO' | 'POT' | 'ONNX' | 'PYTORCH' | 'BASE';

export interface OptimizedModel extends Omit<TrainedModel, OptimizedModelOmitFields> {
    modelStatus: OptimizedModelsDTO['model_status'];
    optimizationObjectives: OptimizedModelsDTO['optimization_objectives'];
    optimizationMethods: OptimizedModelsDTO['optimization_methods'];
    optimizationType: OptimizationTypes;
    configurations: OptimizedModelsDTO['configurations'];
    hasExplainableAI: boolean;
    modelFormat: ModelFormat;
    license: string;
}

export interface ModelDetails {
    labels: Label[];
    trainedModel: TrainedModel;
    optimizedModels: OptimizedModel[];
    trainingDatasetInfo: TrainingDatasetInfo;
    purgeInfo?: {
        isPurged: boolean;
        purgeTime: string | null;
        userId: string | null;
    };
}
