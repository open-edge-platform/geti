// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
