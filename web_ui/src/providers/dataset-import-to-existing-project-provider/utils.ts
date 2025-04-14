// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
