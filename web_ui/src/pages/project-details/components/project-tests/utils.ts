// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { formatDate } from '@shared/utils';

import { Test } from '../../../../core/tests/tests.interface';
import { ColumnCell, TestTableData } from './tests-list.interface';

export const COLUMNS: ColumnCell[] = [
    {
        name: 'Name',
        key: 'testName',
    },
    {
        name: 'Task type',
        key: 'taskType',
    },
    {
        name: 'Model',
        key: 'modelTemplateName',
    },
    {
        name: 'Optimization',
        key: 'optimizationType',
    },
    {
        name: 'Dataset',
        key: 'datasetName',
        width: 110,
    },
    {
        name: 'Labels',
        key: 'numberOfLabels',
        width: 95,
    },
    {
        name: 'Images',
        key: 'numberOfImages',
        width: 95,
    },
    {
        name: 'Frames',
        key: 'numberOfFrames',
        width: 100,
    },
    {
        name: 'Precision',
        key: 'precision',
        width: 120,
    },
    {
        name: 'Score',
        key: 'scoreValue',
        width: 120,
    },
    {
        name: 'Date',
        key: 'creationTime',
    },
    {
        name: 'Submenu',
        key: 'submenu',
    },
];

export const getTestsTableData = (tests: Test[]): TestTableData => {
    return tests.map(
        ({ id, testName, modelInfo, datasetsInfo, creationTime, jobInfo, averagedScore, scoreDescription }) => {
            const {
                groupName,
                modelTemplateName,
                numberOfLabels,
                version,
                optimizationType,
                groupId,
                id: modelId,
                precision,
                taskType,
            } = modelInfo;
            const { datasetName, numberOfImages, numberOfFrames, id: datasetId } = datasetsInfo[0];

            return {
                id,
                version,
                testName,
                datasetId,
                datasetName,
                creationTime,
                modelTemplateName,
                numberOfImages: numberOfImages ?? '-',
                numberOfFrames: numberOfFrames ?? '-',
                numberOfLabels: numberOfLabels ?? '-',
                groupName,
                scoreDescription,
                groupId,
                scoreValue: averagedScore,
                jobStatus: jobInfo.status,
                optimizationType,
                modelId,
                precision,
                taskType,
            };
        }
    );
};

export const formatTestDate = (date: string): string => formatDate(date, 'DD MMM YYYY');

export const formatTestTime = (date: string): string => formatDate(date, 'hh:mm A');

export enum TestNameErrors {
    EMPTY_NAME = 'EMPTY_NAME',
    EXISTING_NAME = 'EXISTING_NAME',
}

export const TEST_NAME_ERRORS: Record<TestNameErrors, string> = {
    [TestNameErrors.EXISTING_NAME]: 'Test name must be unique',
    [TestNameErrors.EMPTY_NAME]: 'Test name cannot be empty',
};
