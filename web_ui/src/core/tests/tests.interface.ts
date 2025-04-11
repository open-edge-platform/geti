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
