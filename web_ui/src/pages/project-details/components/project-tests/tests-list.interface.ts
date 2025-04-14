// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
