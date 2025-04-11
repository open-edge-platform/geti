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
