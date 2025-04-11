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

import { DATASET_IMPORT_STATUSES } from '../../core/datasets/dataset.enum';
import { DatasetImportItem, DatasetImportToExistingProjectItem } from '../../core/datasets/dataset.interface';
import { Label } from '../../core/labels/label.interface';

export const matchStatus = (
    datasetImportItem: DatasetImportItem | undefined,
    statuses: DATASET_IMPORT_STATUSES | DATASET_IMPORT_STATUSES[]
): boolean => [statuses].flat().some((status) => !!datasetImportItem && status === datasetImportItem.status);

export const getLabelsMap = (
    labels: string[],
    projectLabels: Label[]
): DatasetImportToExistingProjectItem['labelsMap'] => {
    const labelsMap: DatasetImportToExistingProjectItem['labelsMap'] = {};

    labels.forEach((labelName) => {
        const label = projectLabels.find(({ name }) => name.toLocaleLowerCase() === labelName.toLocaleLowerCase());

        if (label !== undefined) {
            labelsMap[labelName] = label.id;
        }
    });

    return labelsMap;
};

export const getDatasetImportInitialState = (data: {
    id: string;
    name: string;
    size: string;
    projectId: string;
    datasetId: string;
}): DatasetImportToExistingProjectItem => ({
    ...data,
    labels: [],
    progress: 0,
    warnings: [],
    labelsMap: {},
    uploadId: null,
    datasetName: '',
    startFromBytes: 0,
    startAt: Date.now(),
    timeRemaining: null,
    bytesRemaining: null,
    status: DATASET_IMPORT_STATUSES.UPLOADING,
});
