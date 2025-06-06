// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TASK_TYPE,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
} from '../../core/datasets/dataset.enum';
import {
    DatasetImportSupportedProjectType,
    DatasetImportToNewProjectItem,
} from '../../core/datasets/dataset.interface';

export const getMockedSupportedProjectTypes = (items: DatasetImportSupportedProjectType[]) => {
    return [
        {
            projectType: DATASET_IMPORT_TASK_TYPE.DETECTION_CLASSIFICATION,
            pipeline: {
                connections: [
                    {
                        from: 'Dataset',
                        to: 'Detection',
                    },
                    {
                        from: 'Detection',
                        to: 'Crop',
                    },
                    {
                        from: 'Crop',
                        to: 'Classification',
                    },
                ],
                tasks: [
                    {
                        title: 'Dataset',
                        taskType: DATASET_IMPORT_TASK_TYPE.DATASET,
                        labels: [],
                    },
                    {
                        title: 'Detection',
                        taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                        labels: [],
                    },
                    {
                        title: 'Crop',
                        taskType: DATASET_IMPORT_TASK_TYPE.CROP,
                        labels: [],
                    },
                    {
                        title: 'Classification',
                        taskType: DATASET_IMPORT_TASK_TYPE.CLASSIFICATION,
                        labels: [],
                    },
                ],
            },
        },
        ...items,
    ];
};
export const getMockedUploadItem = (
    item: Partial<DatasetImportToNewProjectItem> = {}
): DatasetImportToNewProjectItem => ({
    id: 'fileTestId',
    name: 'fileTestName',
    taskType: DATASET_IMPORT_TASK_TYPE.DETECTION_CLASSIFICATION,
    supportedProjectTypes: getMockedSupportedProjectTypes(item.supportedProjectTypes ?? []),
    size: '',
    labels: [],
    progress: 0,
    warnings: [],
    uploadId: null,
    projectName: '',
    startFromBytes: 0,
    startAt: Date.now(),
    timeRemaining: null,
    bytesRemaining: null,
    firstChainTaskType: null,
    firstChainLabels: [],
    labelsToSelect: [],
    labelColorMap: {},
    completedSteps: [],
    preparingJobId: null,
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
    openedSteps: [DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET],
    ...item,
});
