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

import { JobInfoStatus } from '../../../../core/tests/dtos/tests.interface';
import { Test } from '../../../../core/tests/tests.interface';

type ColumnsKeys =
    | 'testName'
    | 'taskType'
    | 'groupName'
    | 'groupId'
    | 'modelTemplateName'
    | 'optimizationType'
    | 'datasetName'
    | 'numberOfLabels'
    | 'numberOfImages'
    | 'numberOfFrames'
    | 'scoreValue'
    | 'creationTime'
    | 'submenu'
    | 'modelId'
    | 'precision';

export interface ColumnCell {
    name: string;
    key: ColumnsKeys;
    width?: number;
}

export type TestsTableKeys =
    | Exclude<ColumnsKeys, 'submenu'>
    | 'id'
    | 'jobStatus'
    | 'version'
    | 'scoreDescription'
    | 'datasetId';

type TableRecord = Record<TestsTableKeys, number | string> & { jobStatus: JobInfoStatus };
export type TestTableData = TableRecord[];

export interface TestsTableProps {
    tests: Test[];
    isLoading: boolean;
}
