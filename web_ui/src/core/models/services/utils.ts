// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty, orderBy } from 'lodash-es';

import { getFileSize, isNonEmptyString } from '../../../shared/utils';
import { TrainingDatasetInfoDTO } from '../../datasets/dtos/training-dataset.interface';
import { TrainingDatasetInfo } from '../../datasets/services/training-dataset.interface';
import { getRawNewLabel } from '../../projects/services/utils';
import { PerformanceType } from '../../projects/task.interface';
import { TaskWithSupportedAlgorithms } from '../../supported-algorithms/supported-algorithms.interface';
import {
    ModelDetailsDTO,
    OptimizationTypesDTO,
    OptimizedModelsDTO,
    TrainedModelDTO,
} from '../dtos/model-details.interface';
import { ModelDTO, ModelPerformanceDTO, ModelsDTO } from '../dtos/models.interface';
import { ModelPerformance, ModelsGroups, ModelVersion } from '../models.interface';
import { ModelDetails, OptimizationTypes, OptimizedModel, TrainedModel } from '../optimized-models.interface';

const getPerformance = (performanceDTO: ModelPerformanceDTO): ModelPerformance => {
    if ('local_score' in performanceDTO) {
        return {
            type: PerformanceType.ANOMALY,
            localScore: performanceDTO.local_score,
            globalScore: performanceDTO.global_score,
        };
    }

    return {
        type: PerformanceType.DEFAULT,
        score: performanceDTO.score,
    };
};

const getModelScore = (performance: ModelPerformanceDTO): number | null => {
    const score = 'global_score' in performance ? performance.global_score : performance.score;

    return score;
};

export const getOptimizationType = (type: OptimizationTypesDTO): OptimizationTypes => {
    return type === 'NONE' ? 'BASE' : type;
};

export const getModelsEntity = (
    modelsDTO: ModelsDTO[],
    tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms
): ModelsGroups[] => {
    return modelsDTO.map(({ name, models, id, task_id, model_template_id, lifecycle_stage }) => {
        const sortedModelsByVersion: ModelDTO[] = orderBy(models, 'version', 'desc');

        const algorithms = tasksWithSupportedAlgorithms[task_id] ?? [];
        const usedAlgorithm = algorithms.find((algorithm) => algorithm.modelTemplateId === model_template_id);

        const summary = usedAlgorithm?.summary ?? '';
        const templateName = usedAlgorithm?.templateName ?? '';

        const modelsEntity: ModelVersion[] = sortedModelsByVersion.map((model) => {
            const {
                id: modelId,
                active_model,
                creation_date,
                name: architectureName,
                version,
                label_schema_in_sync,
                purge_info,
                lifecycle_stage: modelLifecycleStage,
                size,
            } = model;

            const performance: ModelPerformance = getPerformance(model.performance);

            return {
                version,
                performance,
                groupName: architectureName,
                id: modelId,
                groupId: id,
                isActiveModel: active_model,
                creationDate: creation_date,
                templateName,
                isLabelSchemaUpToDate: label_schema_in_sync,
                purgeInfo: purge_info
                    ? {
                          isPurged: purge_info.is_purged,
                          purgeTime: purge_info.purge_time,
                          userId: purge_info.user_uid,
                      }
                    : undefined,
                lifecycleStage: modelLifecycleStage,
                modelSize: size,
            };
        });

        return {
            taskId: task_id,
            groupId: id,
            modelSummary: summary,
            groupName: name,
            modelVersions: modelsEntity,
            modelTemplateName: templateName,
            modelTemplateId: model_template_id,
            lifecycleStage: lifecycle_stage,
        };
    });
};

const getTrainedModel = (trainedModel: TrainedModelDTO): TrainedModel => {
    const {
        id,
        name,
        size,
        performance,
        labels,
        precision,
        architecture,
        creation_date,
        training_dataset_info,
        previous_revision_id,
        previous_trained_revision_id,
        version,
        label_schema_in_sync,
        total_disk_size,
        lifecycle_stage,
    } = trainedModel;

    const score = getModelScore(performance);

    return {
        id,
        labels,
        version,
        precision,
        architecture,
        modelName: name,
        creationDate: creation_date,
        previousRevisionId: previous_revision_id,
        isLabelSchemaUpToDate: label_schema_in_sync,
        numberOfFrames: training_dataset_info.n_frames,
        numberOfImages: training_dataset_info.n_images,
        numberOfSamples: training_dataset_info.n_samples,
        modelSize: getFileSize(size),
        totalDiskSize: getFileSize(total_disk_size),
        previousTrainedRevisionId: previous_trained_revision_id,
        accuracy: score,
        license: 'Apache 2.0',
        lifecycleStage: lifecycle_stage,
    };
};

const getOptimizedModelsEntity = (optimizedModels: OptimizedModelsDTO[]): OptimizedModel[] => {
    return optimizedModels.map(
        ({
            id,
            name,
            size,
            labels,
            version,
            precision,
            model_status,
            performance,
            creation_date,
            optimization_type,
            optimization_methods,
            optimization_objectives,
            previous_revision_id,
            previous_trained_revision_id,
            configurations,
            model_format,
            has_xai_head,
            lifecycle_stage,
        }) => {
            const score = getModelScore(performance);

            const isModelReady = model_status === 'SUCCESS';

            return {
                id,
                labels,
                version,
                precision,
                configurations,
                modelName: name,
                hasExplainableAI: has_xai_head,
                modelFormat: model_format,
                modelStatus: model_status,
                creationDate: creation_date,
                performance: getPerformance(performance),
                previousRevisionId: previous_revision_id,
                optimizationMethods: optimization_methods,
                optimizationObjectives: optimization_objectives,
                previousTrainedRevisionId: previous_trained_revision_id,
                optimizationType: getOptimizationType(optimization_type),
                accuracy: isModelReady ? score : null,
                modelSize: isModelReady ? getFileSize(size) : '-',
                license: 'Apache 2.0',
                lifecycleStage: lifecycle_stage,
            };
        }
    );
};

const getTrainingDatasetInfo = (trainingDatasetInfo: TrainingDatasetInfoDTO): TrainingDatasetInfo => {
    return {
        revisionId: trainingDatasetInfo.dataset_revision_id,
        storageId: trainingDatasetInfo.dataset_storage_id,
    };
};

export const getModelEntity = (model: ModelDetailsDTO): ModelDetails => {
    const trainedModel: TrainedModel = getTrainedModel(model);
    const optimizedModels: OptimizedModel[] = getOptimizedModelsEntity(model.optimized_models);
    const trainingDatasetInfo: TrainingDatasetInfo = getTrainingDatasetInfo(model.training_dataset_info);
    const purgeInfo = model.purge_info
        ? {
              isPurged: model.purge_info.is_purged,
              purgeTime: model.purge_info.purge_time,
              userId: model.purge_info.user_uid,
          }
        : undefined;

    return {
        trainedModel,
        optimizedModels,
        labels: model.labels.map(getRawNewLabel),
        trainingDatasetInfo,
        purgeInfo,
    };
};

export const checkModelIntegrity = (model: ModelsGroups) => {
    return (
        model.hasOwnProperty('groupId') &&
        model.hasOwnProperty('modelVersions') &&
        isNonEmptyString(model.groupId) &&
        !isEmpty(model.modelVersions)
    );
};
