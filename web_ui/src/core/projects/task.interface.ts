// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeypointNode } from '../annotations/shapes.interface';
import { LabelTreeItem } from '../labels/label-tree-view.interface';
import { EditedLabel, Label, LabelsRelationType } from '../labels/label.interface';
import { DOMAIN } from './core.interface';

export interface TaskMetadata {
    labels: LabelTreeItem[];
    domain: DOMAIN;
    relation: LabelsRelationType;
    keypointStructure?: {
        edges: { nodes: [string, string] }[];
        positions: { label: string; x: number; y: number }[];
    };
}

interface TaskCommon {
    id: string;
    title: string;
    domain: DOMAIN;
}

export interface EditTask extends TaskCommon {
    labels: EditedLabel[];
}

export interface LabelTask extends TaskCommon {
    labels: Label[];
}

export interface KeypointStructure {
    edges: { nodes: [string, string] }[];
    positions: KeypointNode[];
}

export interface KeypointTask extends LabelTask {
    domain: DOMAIN.KEYPOINT_DETECTION;
    keypointStructure: KeypointStructure;
}

export type Task = LabelTask | KeypointTask;

export enum PerformanceType {
    DEFAULT = 'default_performance',
    ANOMALY = 'anomaly_performance',
}

export interface Score {
    value: number;
    metricType: string;
}

interface PerformanceGeneric {
    type: PerformanceType;
    score: number | null;
}

interface TaskPerformance extends PerformanceGeneric {
    type: PerformanceType.DEFAULT;
    taskPerformances: {
        domain?: DOMAIN;
        taskNodeId: string;
        score: Score | null;
    }[];
}

export interface AnomalyTaskPerformance extends PerformanceGeneric {
    type: PerformanceType.ANOMALY;
    globalScore: number | null;
    localScore: number | null;

    taskPerformances: {
        domain?: DOMAIN;
        taskNodeId: string;
        score: Score | null;
        globalScore: Score | null;
        localScore: Score | null;
    }[];
}

export type Performance = TaskPerformance | AnomalyTaskPerformance;
