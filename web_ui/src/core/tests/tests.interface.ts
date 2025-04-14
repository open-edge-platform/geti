// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TASK_TYPE } from '../projects/dtos/task.interface';
import { JobInfoStatus } from './dtos/tests.interface';

export interface TestScore {
    labelId: string | null;
    name: string;
    value: number;
}

export enum MetricType {
    IMAGE_SCORE = 'Image score',
    OBJECT_SCORE = 'Object score',
}

export interface Test {
    id: string;
    testName: string;
    creationTime: string;
    jobInfo: {
        id: string;
        status: JobInfoStatus;
    };
    modelInfo: {
        id: string;
        groupId: string;
        groupName: string;
        modelTemplateId: string;
        modelTemplateName: string;
        taskType: TASK_TYPE;
        numberOfLabels: number;
        version: number;
        optimizationType: string;
        creationDate: string;
        precision: string;
    };
    datasetsInfo: {
        id: string;
        isDeleted: boolean;
        datasetName: string;
        numberOfImages: number;
        numberOfFrames: number;
        numberOfSamples: number;
    }[];
    scores: TestScore[];
    averagedScore: number;
    scoreDescription: string;
}
