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

import { SearchOptionsRule, SearchOptionsRuleDTO } from '../../media/media-filter.interface';
import { DATASET_IMPORT_TASK_TYPE } from '../dataset.enum';
import {
    DatasetImportConnection,
    DatasetImportLabel,
    DatasetImportPipeline,
    DatasetImportSupportedProjectType,
    DatasetImportTask,
    DatasetImportWarning,
} from '../dataset.interface';
import { DATASET_IMPORT_TASK_TYPE_DTO } from '../dtos/dataset.enum';
import {
    DatasetImportConnectionDTO,
    DatasetImportLabelDTO,
    DatasetImportPipelineDTO,
    DatasetImportSupportedProjectTypeDTO,
    DatasetImportTaskDTO,
    DatasetImportWarningDTO,
} from '../dtos/dataset.interface';
import { TrainingDatasetDTO } from '../dtos/training-dataset.interface';
import { TrainingDatasetRevision } from './training-dataset.interface';

const TASK_TYPE_FROM_TASK_TYPE_DTO: Record<DATASET_IMPORT_TASK_TYPE_DTO, DATASET_IMPORT_TASK_TYPE> = {
    [DATASET_IMPORT_TASK_TYPE_DTO.CROP]: DATASET_IMPORT_TASK_TYPE.CROP,
    [DATASET_IMPORT_TASK_TYPE_DTO.DATASET]: DATASET_IMPORT_TASK_TYPE.DATASET,
    [DATASET_IMPORT_TASK_TYPE_DTO.DETECTION]: DATASET_IMPORT_TASK_TYPE.DETECTION,
    [DATASET_IMPORT_TASK_TYPE_DTO.DETECTION_CLASSIFICATION]: DATASET_IMPORT_TASK_TYPE.DETECTION_CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE_DTO.DETECTION_SEGMENTATION]: DATASET_IMPORT_TASK_TYPE.DETECTION_SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE_DTO.DETECTION_ROTATED_BOUNDING_BOX]:
        DATASET_IMPORT_TASK_TYPE.DETECTION_ROTATED_BOUNDING_BOX,
    [DATASET_IMPORT_TASK_TYPE_DTO.CLASSIFICATION]: DATASET_IMPORT_TASK_TYPE.CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE_DTO.CLASSIFICATION_HIERARCHICAL]: DATASET_IMPORT_TASK_TYPE.CLASSIFICATION_HIERARCHICAL,
    [DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY_CLASSIFICATION]: DATASET_IMPORT_TASK_TYPE.ANOMALY_CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY_DETECTION]: DATASET_IMPORT_TASK_TYPE.ANOMALY_DETECTION,
    [DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY_SEGMENTATION]: DATASET_IMPORT_TASK_TYPE.ANOMALY_SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION]: DATASET_IMPORT_TASK_TYPE.SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION_INSTANCE]: DATASET_IMPORT_TASK_TYPE.SEGMENTATION_INSTANCE,
    [DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY]: DATASET_IMPORT_TASK_TYPE.ANOMALY_CLASSIFICATION,
};

const TASK_TYPE_DTO_FROM_TASK_TYPE: Record<DATASET_IMPORT_TASK_TYPE, DATASET_IMPORT_TASK_TYPE_DTO> = {
    [DATASET_IMPORT_TASK_TYPE.CROP]: DATASET_IMPORT_TASK_TYPE_DTO.CROP,
    [DATASET_IMPORT_TASK_TYPE.DATASET]: DATASET_IMPORT_TASK_TYPE_DTO.DATASET,
    [DATASET_IMPORT_TASK_TYPE.DETECTION]: DATASET_IMPORT_TASK_TYPE_DTO.DETECTION,
    [DATASET_IMPORT_TASK_TYPE.DETECTION_CLASSIFICATION]: DATASET_IMPORT_TASK_TYPE_DTO.DETECTION_CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE.DETECTION_SEGMENTATION]: DATASET_IMPORT_TASK_TYPE_DTO.DETECTION_SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE.DETECTION_ROTATED_BOUNDING_BOX]:
        DATASET_IMPORT_TASK_TYPE_DTO.DETECTION_ROTATED_BOUNDING_BOX,
    [DATASET_IMPORT_TASK_TYPE.CLASSIFICATION]: DATASET_IMPORT_TASK_TYPE_DTO.CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE.CLASSIFICATION_HIERARCHICAL]: DATASET_IMPORT_TASK_TYPE_DTO.CLASSIFICATION_HIERARCHICAL,
    [DATASET_IMPORT_TASK_TYPE.ANOMALY_CLASSIFICATION]: DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY_CLASSIFICATION,
    [DATASET_IMPORT_TASK_TYPE.ANOMALY_DETECTION]: DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY_DETECTION,
    [DATASET_IMPORT_TASK_TYPE.ANOMALY_SEGMENTATION]: DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY_SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE.SEGMENTATION]: DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION,
    [DATASET_IMPORT_TASK_TYPE.SEGMENTATION_INSTANCE]: DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION_INSTANCE,
};

export const getTaskTypeDTOFromTaskType = (
    taskType: DATASET_IMPORT_TASK_TYPE,
    anomalyRevamp: boolean
): DATASET_IMPORT_TASK_TYPE_DTO => {
    if (
        anomalyRevamp &&
        [
            DATASET_IMPORT_TASK_TYPE.ANOMALY_DETECTION,
            DATASET_IMPORT_TASK_TYPE.ANOMALY_SEGMENTATION,
            DATASET_IMPORT_TASK_TYPE.ANOMALY_CLASSIFICATION,
        ].includes(taskType)
    ) {
        return DATASET_IMPORT_TASK_TYPE_DTO.ANOMALY;
    }
    return TASK_TYPE_DTO_FROM_TASK_TYPE[taskType];
};

export const getTrainingDatasetRevisionData = (data: TrainingDatasetDTO): TrainingDatasetRevision => {
    return {
        id: data.id,
        trainingSubset: data.subset_info.training,
        testingSubset: data.subset_info.testing,
        validationSubset: data.subset_info.validation,
    };
};

export const mapSearchRulesToDto = (rules: SearchOptionsRule[]): SearchOptionsRuleDTO[] => {
    return rules.map((rule) => {
        const { field, operator, value } = rule;

        return {
            field: field.toLocaleLowerCase(),
            operator: operator.toLocaleLowerCase(),
            // The backend does not accept integer numbers and AXIOS serializes
            // the body as JSON, therefore we apply a hack for filtering on 0.0 and 1.0.
            value: value === 0 ? 10e-9 : value === 1 ? 1 - 10e-9 : value,
        };
    });
};

export const getWarningsFromDTO = (warningsDTO: DatasetImportWarningDTO[] = []): DatasetImportWarning[] => {
    return warningsDTO.map(
        (warningDTO: DatasetImportWarningDTO): DatasetImportWarning => ({
            type: warningDTO.type,
            name: warningDTO.name,
            description: warningDTO.description,
            affectedImages: warningDTO.affected_images,
            resolveStrategy: warningDTO.resolve_strategy,
        })
    );
};

const getProjectTypeFromDTO = (projectType: string): string => {
    if (projectType === 'anomaly') {
        return 'anomaly_classification';
    }

    return projectType;
};

export const getSupportedProjectTypesFromDTO = (
    supportedProjectTypesDTO: DatasetImportSupportedProjectTypeDTO[] = []
): DatasetImportSupportedProjectType[] => {
    const getLabelsFromDTO = (labelsDTO: DatasetImportLabelDTO[]): DatasetImportLabel[] => {
        return labelsDTO.map(
            (labelDTO: DatasetImportLabelDTO): DatasetImportLabel => ({
                name: labelDTO.name,
                color: labelDTO.color,
                group: labelDTO.group,
                parent: labelDTO.parent,
            })
        );
    };

    const getTasksFromDTO = (tasksDTO: DatasetImportTaskDTO[]): DatasetImportTask[] => {
        return tasksDTO.map(
            (taskDTO: DatasetImportTaskDTO): DatasetImportTask => ({
                title: taskDTO.title,
                taskType: TASK_TYPE_FROM_TASK_TYPE_DTO[taskDTO.task_type],
                labels: getLabelsFromDTO(taskDTO.labels),
            })
        );
    };

    const getConnectionsFromDTO = (connectionsDTO: DatasetImportConnectionDTO[]): DatasetImportConnection[] => {
        return connectionsDTO.map(
            (connectionDTO: DatasetImportConnectionDTO): DatasetImportConnection => ({
                from: connectionDTO.from,
                to: connectionDTO.to,
            })
        );
    };

    const getPipelineFromDTO = (pipelineDTO: DatasetImportPipelineDTO): DatasetImportPipeline => ({
        tasks: getTasksFromDTO(pipelineDTO.tasks),
        connections: getConnectionsFromDTO(pipelineDTO.connections),
    });

    return supportedProjectTypesDTO.map(
        (supportedProjectTypeDTO: DatasetImportSupportedProjectTypeDTO): DatasetImportSupportedProjectType => ({
            projectType: getProjectTypeFromDTO(supportedProjectTypeDTO.project_type),
            pipeline: getPipelineFromDTO(supportedProjectTypeDTO.pipeline),
        })
    );
};
