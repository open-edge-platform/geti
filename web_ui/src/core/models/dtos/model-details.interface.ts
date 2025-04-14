// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TrainingDatasetInfoDTO } from '../../datasets/dtos/training-dataset.interface';
import { LabelDTO } from '../../labels/dtos/label.interface';
import { ModelDTO } from './models.interface';

type ModelStatus = 'SUCCESS' | 'FAILED' | 'NOT_IMPROVED' | 'NOT_READY' | 'TRAINED_NO_STATS';

export interface TrainedModelDTO extends Omit<ModelDTO, 'active_model'> {
    labels: LabelDTO[];
    architecture: string;
    precision: string[];
    previous_revision_id: string;
    previous_trained_revision_id: string;
    label_schema_in_sync: boolean;
    training_dataset_info: TrainingDatasetInfoDTO;
}

type OptimizationMethods = 'FILTER_PRUNING' | 'QUANTIZATION';

export type OptimizationTypesDTO = 'MO' | 'POT' | 'NONE';

interface AccuracyDropConfiguration {
    name: 'max_accuracy_drop';
    value: number;
}

export enum ModelFormat {
    OpenVINO = 'OpenVINO',
    Pytorch = 'PYTORCH',
    ONNX = 'ONNX',
}

export interface OptimizedModelsDTO
    extends Omit<TrainedModelDTO, 'architecture' | 'training_dataset_info' | 'label_schema_in_sync'> {
    model_status: Exclude<ModelStatus, 'NOT_IMPROVED'>;
    optimization_objectives: Record<string, string>;
    optimization_methods: OptimizationMethods[];
    optimization_type: OptimizationTypesDTO;
    configurations: AccuracyDropConfiguration[];
    has_xai_head: boolean;
    model_format: ModelFormat;
}

export interface ModelDetailsDTO extends TrainedModelDTO {
    optimized_models: OptimizedModelsDTO[];
}
