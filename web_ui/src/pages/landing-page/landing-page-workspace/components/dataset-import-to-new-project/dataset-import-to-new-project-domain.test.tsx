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

import { fireEvent, render, screen } from '@testing-library/react';
import capitalize from 'lodash/capitalize';

import {
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TASK_TYPE,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
} from '../../../../../core/datasets/dataset.enum';
import { DatasetImportToNewProjectItem } from '../../../../../core/datasets/dataset.interface';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { DatasetImportToNewProjectDomain } from './dataset-import-to-new-project-domain.component';

const mockProjects: ProjectProps[] = [
    getMockedProject({
        id: '111111',
        name: 'Test project 1',
    }),
    getMockedProject({
        id: '222222',
        name: 'Test project 2',
    }),
];

const getMockedUploadItem = (item: Partial<DatasetImportToNewProjectItem> = {}): DatasetImportToNewProjectItem => ({
    id: 'fileTestId',
    name: 'fileTestName',
    taskType: DATASET_IMPORT_TASK_TYPE.DETECTION_CLASSIFICATION,
    supportedProjectTypes: [
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
    ],
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

describe('DatasetImportToNewProjectDomain', () => {
    const mockPatchUpload = jest.fn();

    const mockUploadItem = getMockedUploadItem({
        id: 'fileTestId',
        name: 'fileTestName',
        taskType: null,
        supportedProjectTypes: [
            {
                projectType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                pipeline: {
                    connections: [
                        {
                            from: 'dataset_0',
                            to: 'detection_1',
                        },
                    ],
                    tasks: [
                        {
                            title: 'dataset_0',
                            taskType: DATASET_IMPORT_TASK_TYPE.DATASET,
                            labels: [],
                        },
                        {
                            title: 'detection_1',
                            taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
                            labels: [
                                {
                                    name: 'test',
                                    group: 'Detection labels',
                                },
                            ],
                        },
                    ],
                },
            },
        ],
    });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders one error message at the time', () => {
        render(
            <DatasetImportToNewProjectDomain
                datasetImportItem={mockUploadItem}
                patchDatasetImport={mockPatchUpload}
                anomalyRevamp={false}
            />
        );
        const [projectOne] = mockProjects;
        const input = screen.getByLabelText('Project name');

        fireEvent.change(input, { target: { value: projectOne.name } });
        expect(screen.queryByText(`Project '${projectOne.name}' already exists`)).not.toBeInTheDocument();
    });

    it('task type should have a default value if upload item got task type from the server', () => {
        const taskType = DATASET_IMPORT_TASK_TYPE.DETECTION;

        render(
            <DatasetImportToNewProjectDomain
                datasetImportItem={{ ...mockUploadItem, taskType }}
                patchDatasetImport={mockPatchUpload}
                anomalyRevamp={false}
            />
        );

        expect(screen.getByText(capitalize(taskType))).toBeInTheDocument();
    });

    it('if upload item has no taskType and we have only one to assign, it should be assigned automatically', () => {
        render(
            <DatasetImportToNewProjectDomain
                datasetImportItem={mockUploadItem}
                patchDatasetImport={mockPatchUpload}
                anomalyRevamp={false}
            />
        );
        expect(mockPatchUpload).toHaveBeenNthCalledWith(
            1,
            expect.objectContaining({
                id: mockUploadItem.id,
                projectName: 'Project',
            })
        );

        expect(mockPatchUpload).toHaveBeenNthCalledWith(
            2,
            expect.objectContaining({
                id: mockUploadItem.id,
                labels: [{ group: 'Detection labels', name: 'test' }],
                firstChainLabels: [],
                firstChainTaskType: null,
                taskType: 'detection',
                labelsToSelect: [{ group: 'Detection labels', name: 'test' }],
                labelColorMap: expect.objectContaining({ test: expect.any(String) }),
            })
        );
    });

    it('task type should not have a default value if we have more than one task to select', () => {
        const mockUploadItemWithTwoTasks = getMockedUploadItem({
            ...mockUploadItem,
            supportedProjectTypes: [
                {
                    projectType: DATASET_IMPORT_TASK_TYPE.DETECTION,
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
                        ],
                    },
                },
                {
                    projectType: DATASET_IMPORT_TASK_TYPE.DETECTION_ROTATED_BOUNDING_BOX,
                    pipeline: {
                        connections: [
                            {
                                from: 'Dataset',
                                to: 'Detection',
                            },
                            {
                                from: 'Detection oriented',
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
                                title: 'Detection oriented',
                                taskType: DATASET_IMPORT_TASK_TYPE.DETECTION_ROTATED_BOUNDING_BOX,
                                labels: [],
                            },
                        ],
                    },
                },
            ],
            taskType: null,
        });

        render(
            <DatasetImportToNewProjectDomain
                datasetImportItem={mockUploadItemWithTwoTasks}
                patchDatasetImport={mockPatchUpload}
                anomalyRevamp={false}
            />
        );

        expect(
            screen.queryByText(capitalize(mockUploadItemWithTwoTasks.supportedProjectTypes[0].projectType))
        ).not.toBeInTheDocument();
        expect(
            screen.queryByText(capitalize(mockUploadItemWithTwoTasks.supportedProjectTypes[1].projectType))
        ).not.toBeInTheDocument();
    });

    it('it selects all labels by default on a task chain project', () => {
        const detectionLabels = [
            {
                name: 'Fish',
                group: 'Detection labels',
            },
        ];
        const classificationLabels = [
            {
                name: 'RedYellowFish',
                group: 'Fish',
            },
            {
                name: 'SiameseFish',
                group: 'Fish',
            },
            {
                name: 'BlueFish',
                group: 'Fish',
            },
            {
                name: 'YellowFish',
                group: 'Fish',
            },
            {
                name: 'Tuna',
                group: 'Fish',
            },
            {
                name: 'ClownFish',
                group: 'Fish',
            },
            {
                name: 'GoldFish',
                group: 'Fish',
            },
        ];

        const mockUploadItemTaskChain = getMockedUploadItem({
            id: 'fileTestId',
            name: 'fileTestName',
            taskType: null,
            supportedProjectTypes: [
                {
                    projectType: 'detection_classification',
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
                                labels: detectionLabels,
                            },
                            {
                                title: 'Crop',
                                taskType: DATASET_IMPORT_TASK_TYPE.CROP,
                                labels: [],
                            },
                            {
                                title: 'Classification',
                                taskType: DATASET_IMPORT_TASK_TYPE.CLASSIFICATION,
                                labels: classificationLabels,
                            },
                        ],
                    },
                },
            ],
        });

        render(
            <DatasetImportToNewProjectDomain
                datasetImportItem={mockUploadItemTaskChain}
                patchDatasetImport={mockPatchUpload}
                anomalyRevamp={false}
            />
        );

        expect(mockPatchUpload).toHaveBeenNthCalledWith(
            2,
            expect.objectContaining({
                id: mockUploadItem.id,
                labels: [...detectionLabels, ...classificationLabels],
                firstChainLabels: detectionLabels,
                firstChainTaskType: 'detection',
                taskType: 'detection_classification',
                labelsToSelect: classificationLabels,
            })
        );
    });
});
