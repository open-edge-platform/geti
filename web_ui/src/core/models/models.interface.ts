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

import { ProjectIdentifier } from '../projects/core.interface';
import { PerformanceType } from '../projects/task.interface';
import { LifecycleStage, PerformanceCategory } from '../supported-algorithms/dtos/supported-algorithms.interface';

export interface TaskPerformance {
    type: PerformanceType.DEFAULT;
    score: number | null;
}
interface AnomalyTaskPerformance {
    type: PerformanceType.ANOMALY;
    globalScore: number | null;
    localScore: number | null;
}

export type ModelPerformance = TaskPerformance | AnomalyTaskPerformance;

export interface ModelVersion {
    id: string;
    performance: ModelPerformance;
    version: number;
    isActiveModel: boolean;
    creationDate: string;
    groupId: string;
    groupName: string;
    templateName: string;
    isLabelSchemaUpToDate: boolean;
    purgeInfo?: {
        userId: null | string;
        isPurged: boolean;
        purgeTime: null | string;
    };
    modelSize: number;
}

export interface ModelsGroups {
    groupId: string;
    taskId: string;
    groupName: string;
    modelTemplateId: string;
    modelTemplateName: string;
    modelVersions: ModelVersion[];
    modelSummary: string;
    lifecycleStage: LifecycleStage;
}

export interface ModelGroupsAlgorithmDetails extends ModelsGroups {
    isDefaultAlgorithm: boolean;
    performanceCategory: PerformanceCategory;
    complexity: number | null;
}

export interface ModelGroupIdentifier extends ProjectIdentifier {
    groupId: string;
}

export interface ModelIdentifier extends ModelGroupIdentifier {
    modelId: string;
}
