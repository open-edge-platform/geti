// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DATASET_IMPORT_TASK_TYPE_DTO } from '../../../src/core/datasets/dtos/dataset.enum';
import { DatasetImportSupportedProjectTypeDTO } from '../../../src/core/datasets/dtos/dataset.interface';
import { JobGeneralPropsDTO } from '../../../src/core/jobs/dtos/jobs-dto.interface';
import { JobState, JobStepState } from '../../../src/core/jobs/jobs.const';
import { getMockedDatasetDTO } from '../../../src/test-utils/mocked-items-factory/mocked-datasets';
import { project } from '../../mocks/classification/mocks';

export { project } from '../../mocks/classification/mocks';
export { project as taskChainProject } from '../../mocks/detection-segmentation/mocks';

export const mockedTestingSet1 = getMockedDatasetDTO({ id: '62aafeed23967484a61caa0a', name: 'Testing set 1' });

export const projectWithTwoDatasets = {
    ...project,
    datasets: [...project.datasets, mockedTestingSet1],
};

export const projectWithFiveDatasets = {
    ...project,
    datasets: [
        ...project.datasets,
        mockedTestingSet1,
        getMockedDatasetDTO({ id: '62aafeed23967484a61caa02', name: 'Testing set 2' }),
        getMockedDatasetDTO({ id: '62aafeed23967484a61caa03', name: 'Testing set 3' }),
        getMockedDatasetDTO({ id: '62aafeed23967484a61caa04', name: 'Testing set 4' }),
        getMockedDatasetDTO({ id: '62aafeed23967484a61caa05', name: 'Testing set 5' }),
    ],
};

export const projectWithSixDatasets = {
    ...project,
    datasets: [
        ...projectWithFiveDatasets.datasets,
        getMockedDatasetDTO({ id: '62aafeed23967484a61caa06', name: 'Testing set 6' }),
    ],
};

export const projects = {
    next_page: '',
    project_counts: 1,
    project_page_count: 1,
    projects: [projectWithTwoDatasets],
};

export const supportedProjectTypesSingleTask: DatasetImportSupportedProjectTypeDTO[] = [
    {
        project_type: 'classification',
        pipeline: {
            connections: [],
            tasks: [
                {
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.CLASSIFICATION,
                    title: 'Classification 1',
                    labels: [
                        { name: 'Guitars' },

                        { name: 'Single Cut', group: 'Electric', parent: 'Guitars' },
                        { name: 'PRS Custom 22', group: 'PRS', parent: 'Single Cut' },
                        { name: 'PRS Custom 24', group: 'PRS', parent: 'Single Cut' },
                        { name: 'Gibson Les Paul Traditional', group: 'Gibson', parent: 'Single Cut' },
                        { name: 'Gibson Les Paul Studio', group: 'Gibson', parent: 'Single Cut' },
                        { name: 'Gibson Les Paul Tribute', group: 'Gibson', parent: 'Single Cut' },
                        { name: 'Fender Telecaster Nashville', group: 'Fender', parent: 'Single Cut' },
                        { name: 'Fender Jazzmaster', group: 'Fender', parent: 'Single Cut' },

                        { name: 'Double Cut', group: 'Electric', parent: 'Guitars' },
                        { name: 'Fender Stratocaster Player', group: 'Fender', parent: 'Double Cut' },
                        { name: 'Ibanez RG', group: 'Ibanez', parent: 'Double Cut' },
                        { name: 'Ibanez AZ', group: 'Ibanez', parent: 'Double Cut' },
                        { name: 'Ibanez RG421-AHM', parent: 'Ibanez RG' },
                        { name: 'Ibanez AZ2204-ICM', parent: 'Ibanez AZ' },

                        { name: 'Hollow', group: 'Acoustic', parent: 'Guitars' },
                        { name: 'PRS SE Hollowbody', group: 'PRS', parent: 'Hollow' },
                    ],
                },
            ],
        },
    },
];

export const supportedProjectTypesTaskChained: DatasetImportSupportedProjectTypeDTO[] = [
    {
        project_type: 'segmentation',
        pipeline: {
            connections: [
                {
                    from: 'Dataset',
                    to: 'Segmentation',
                },
            ],
            tasks: [
                {
                    title: 'Dataset',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DATASET,
                    labels: [],
                },
                {
                    title: 'Segmentation',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION,
                    labels: [
                        {
                            name: 'dog',
                            group: 'default - Segmentation',
                        },
                        {
                            name: 'cat',
                            group: 'default - Segmentation',
                        },
                    ],
                },
            ],
        },
    },
    {
        project_type: 'detection',
        pipeline: {
            connections: [
                {
                    from: 'Dataset',
                    to: 'Detection',
                },
            ],
            tasks: [
                {
                    title: 'Dataset',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DATASET,
                    labels: [],
                },
                {
                    title: 'Detection',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DETECTION,
                    labels: [
                        {
                            name: 'dog',
                            group: 'Detection Task Labels',
                        },
                        {
                            name: 'cat',
                            group: 'Detection Task Labels',
                        },
                    ],
                },
            ],
        },
    },
    {
        project_type: 'instance_segmentation',
        pipeline: {
            connections: [
                {
                    from: 'Dataset',
                    to: 'Instance Segmentation',
                },
            ],
            tasks: [
                {
                    title: 'Dataset',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DATASET,
                    labels: [],
                },
                {
                    title: 'Instance Segmentation',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION_INSTANCE,
                    labels: [
                        {
                            name: 'dog',
                            group: 'Instance Segmentation Task Labels',
                        },
                        {
                            name: 'cat',
                            group: 'Instance Segmentation Task Labels',
                        },
                    ],
                },
            ],
        },
    },
    {
        project_type: 'detection_segmentation',
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
                    to: 'Segmentation',
                },
            ],
            tasks: [
                {
                    title: 'Dataset',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DATASET,
                    labels: [],
                },
                {
                    title: 'Detection',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.DETECTION,
                    labels: [
                        {
                            name: 'detection label',
                            group: 'Detection Task Labels',
                        },
                    ],
                },
                {
                    title: 'Crop',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.CROP,
                    labels: [],
                },
                {
                    title: 'Segmentation',
                    task_type: DATASET_IMPORT_TASK_TYPE_DTO.SEGMENTATION,
                    labels: [
                        {
                            name: 'dog',
                            group: 'Segmentation Task Labels',
                        },
                        {
                            name: 'cat',
                            group: 'Segmentation Task Labels',
                        },
                    ],
                },
            ],
        },
    },
];

export const getMockedJob = (job: Partial<JobGeneralPropsDTO> = {}): JobGeneralPropsDTO => {
    return {
        id: 'job-1',
        name: 'Mocked task job',
        state: JobState.SCHEDULED,
        start_time: '20/03/2022',
        author: 'admin@intel.com',
        creation_time: '20/03/2022',
        end_time: null,
        steps: [
            {
                index: 0,
                message: '',
                progress: -1,
                state: JobStepState.RUNNING,
                step_name: '',
            },
        ],
        cancellation_info: {
            is_cancelled: false,
            user_uid: null,
            cancel_time: null,
            cancellable: true,
        },
        ...job,
    };
};

export const taskChainDetectionSegmentationProject = {
    id: '4dc8f244b7bfafc65898ed27',
    name: 'Candy',
    creation_time: '2025-03-03T07:04:48.951000+00:00',
    creator_id: '9cd4a283-a7d3-44b8-894d-5e60b0d877fc',
    pipeline: {
        tasks: [
            {
                id: '4dc8f244b7bfafc65898ed28',
                title: 'Dataset',
                task_type: 'dataset',
            },
            {
                id: '4dc8f244b7bfafc65898ed2a',
                title: 'Detection',
                task_type: 'detection',
                labels: [
                    {
                        id: '4dc8f244b7bfafc65898ed2c',
                        name: 'Candy',
                        is_anomalous: false,
                        color: '#e96115ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Detection labels',
                        parent_id: null,
                    },
                    {
                        id: '4dc8f244b7bfafc65898ed36',
                        name: 'No object',
                        is_anomalous: false,
                        color: '#000000ff',
                        hotkey: '',
                        is_empty: true,
                        group: 'No object',
                        parent_id: null,
                    },
                ],
                label_schema_id: '4dcd18d7b7bfafc65898ee01',
            },
            {
                id: '4dc8f244b7bfafc65898ed31',
                title: 'Crop',
                task_type: 'crop',
            },
            {
                id: '4dc8f244b7bfafc65898ed2d',
                title: 'Segmentation',
                task_type: 'segmentation',
                labels: [
                    {
                        id: '4dc8f244b7bfafc65898ed2f',
                        name: 'pruple',
                        is_anomalous: false,
                        color: '#9b5de5ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Detection labels___Segmentation labels',
                        parent_id: null,
                    },
                    {
                        id: '4dc8f244b7bfafc65898ed30',
                        name: 'green',
                        is_anomalous: false,
                        color: '#77e65eff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Detection labels___Segmentation labels',
                        parent_id: null,
                    },
                    {
                        id: '4dc8f244b7bfafc65898ed3a',
                        name: 'Empty',
                        is_anomalous: false,
                        color: '#000000ff',
                        hotkey: '',
                        is_empty: true,
                        group: 'Empty',
                        parent_id: null,
                    },
                    {
                        id: '4dcd18d7b7bfafc65898edfd',
                        name: 'orange',
                        is_anomalous: false,
                        color: '#e96115ff',
                        hotkey: '',
                        is_empty: false,
                        group: 'Detection labels___Segmentation labels',
                        parent_id: null,
                    },
                ],
                label_schema_id: '4dcd18d7b7bfafc65898ee04',
            },
        ],
        connections: [
            {
                from: '4dc8f244b7bfafc65898ed28',
                to: '4dc8f244b7bfafc65898ed2a',
            },
            {
                from: '4dc8f244b7bfafc65898ed2a',
                to: '4dc8f244b7bfafc65898ed31',
            },
            {
                from: '4dc8f244b7bfafc65898ed31',
                to: '4dc8f244b7bfafc65898ed2d',
            },
        ],
    },
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/865904c7-632e-4030-8498-9343321edee0/workspaces/a6e442d0-59f6-4cbf-94a1-8046dd62f0ef/projects/4dc8f244b7bfafc65898ed27/thumbnail',
    performance: {
        score: 0.8622612638102195,
        task_performances: [
            {
                task_id: '4dc8f244b7bfafc65898ed2a',
                score: {
                    value: 0.7499999999999998,
                    metric_type: 'f-measure',
                },
            },
            {
                task_id: '4dc8f244b7bfafc65898ed2d',
                score: {
                    value: 0.9745225276204392,
                    metric_type: 'Dice Average',
                },
            },
        ],
    },
    storage_info: {},
    datasets: [
        {
            id: '4dc8f244b7bfafc65898ed33',
            name: 'Dataset',
            use_for_training: true,
            creation_time: '2025-03-03T07:04:48.951000+00:00',
        },
    ],
};

export const detectionStatistics = {
    images: 20,
    videos: 8,
    annotated_images: 7,
    annotated_videos: 6,
    annotated_frames: 1,
    objects_per_label: [
        {
            id: '4dc8f244b7bfafc65898ed2c',
            name: 'Candy',
            color: '#e96115ff',
            value: 24,
        },
        {
            id: '4dc8f244b7bfafc65898ed36',
            name: 'No object',
            color: '#000000ff',
            value: 6,
        },
    ],
    images_and_frames_per_label: [
        {
            id: '4dc8f244b7bfafc65898ed2c',
            name: 'Candy',
            color: '#e96115ff',
            value: 1,
        },
        {
            id: '4dc8f244b7bfafc65898ed36',
            name: 'No object',
            color: '#000000ff',
            value: 0,
        },
    ],
    object_size_distribution_per_label: [
        {
            id: '4dc8f244b7bfafc65898ed2c',
            name: 'Candy',
            color: '#e96115ff',
            size_distribution: [
                [247, 214],
                [184, 172],
                [233, 244],
                [238, 238],
                [212, 149],
                [250, 184],
                [266, 239],
                [223, 157],
                [173, 160],
                [189, 177],
                [190, 172],
                [172, 145],
                [203, 214],
                [265, 256],
                [281, 242],
                [211, 177],
                [266, 254],
                [240, 175],
                [194, 150],
                [156, 153],
                [183, 139],
                [205, 174],
                [235, 247],
                [243, 248],
            ],
            cluster_center: [219, 195],
            cluster_width_height: [68, 80],
            aspect_ratio_threshold_tall: 8.9,
            aspect_ratio_threshold_wide: 0.09,
            object_distribution_from_aspect_ratio: {
                tall: 2,
                balanced: 18,
                wide: 4,
            },
        },
        {
            id: '4dc8f244b7bfafc65898ed36',
            name: 'No object',
            color: '#000000ff',
            size_distribution: [],
            cluster_center: [],
            cluster_width_height: [],
            aspect_ratio_threshold_tall: null,
            aspect_ratio_threshold_wide: null,
            object_distribution_from_aspect_ratio: {
                tall: 0,
                balanced: 0,
                wide: 0,
            },
        },
    ],
};

export const segmentationStatistics = {
    images: 20,
    videos: 8,
    annotated_images: 4,
    annotated_videos: 6,
    annotated_frames: 2,
    objects_per_label: [
        {
            id: '4dc8f244b7bfafc65898ed2f',
            name: 'pruple',
            color: '#9b5de5ff',
            value: 8,
        },
        {
            id: '4dc8f244b7bfafc65898ed30',
            name: 'green',
            color: '#77e65eff',
            value: 11,
        },
        {
            id: '4dcd18d7b7bfafc65898edfd',
            name: 'orange',
            color: '#e96115ff',
            value: 3,
        },
        {
            id: '4dc8f244b7bfafc65898ed3a',
            name: 'Empty',
            color: '#000000ff',
            value: 2,
        },
    ],
    images_and_frames_per_label: [
        {
            id: '4dc8f244b7bfafc65898ed2f',
            name: 'pruple',
            color: '#9b5de5ff',
            value: 1,
        },
        {
            id: '4dc8f244b7bfafc65898ed30',
            name: 'green',
            color: '#77e65eff',
            value: 1,
        },
        {
            id: '4dc8f244b7bfafc65898ed3a',
            name: 'Empty',
            color: '#000000ff',
            value: 0,
        },
        {
            id: '4dcd18d7b7bfafc65898edfd',
            name: 'orange',
            color: '#e96115ff',
            value: 0,
        },
    ],
    object_size_distribution_per_label: [
        {
            id: '4dc8f244b7bfafc65898ed2f',
            name: 'pruple',
            color: '#9b5de5ff',
            size_distribution: [
                [221, 205],
                [205, 174],
                [181, 145],
                [225, 214],
                [217, 202],
                [181, 137],
                [197, 148],
                [175, 134],
            ],
            cluster_center: [200, 170],
            cluster_width_height: [37, 62],
            aspect_ratio_threshold_tall: 8.5,
            aspect_ratio_threshold_wide: 0.08,
            object_distribution_from_aspect_ratio: {
                tall: 0,
                balanced: 8,
                wide: 0,
            },
        },
        {
            id: '4dc8f244b7bfafc65898ed30',
            name: 'green',
            color: '#77e65eff',
            size_distribution: [
                [187, 119],
                [197, 176],
                [155, 117],
                [161, 109],
                [153, 130],
                [247, 199],
                [189, 144],
                [229, 202],
                [221, 208],
                [225, 211],
                [226, 155],
            ],
            cluster_center: [199, 161],
            cluster_width_height: [63, 76],
            aspect_ratio_threshold_tall: 8.09,
            aspect_ratio_threshold_wide: 0.08,
            object_distribution_from_aspect_ratio: {
                tall: 0,
                balanced: 11,
                wide: 0,
            },
        },
        {
            id: '4dc8f244b7bfafc65898ed3a',
            name: 'Empty',
            color: '#000000ff',
            size_distribution: [],
            cluster_center: [],
            cluster_width_height: [],
            aspect_ratio_threshold_tall: null,
            aspect_ratio_threshold_wide: null,
            object_distribution_from_aspect_ratio: {
                tall: 0,
                balanced: 0,
                wide: 0,
            },
        },
        {
            id: '4dcd18d7b7bfafc65898edfd',
            name: 'orange',
            color: '#e96115ff',
            size_distribution: [],
            cluster_center: [],
            cluster_width_height: [],
            aspect_ratio_threshold_tall: null,
            aspect_ratio_threshold_wide: null,
            object_distribution_from_aspect_ratio: {
                tall: 0,
                balanced: 0,
                wide: 0,
            },
        },
    ],
};

export const datasetStatistics = {
    '4dc8f244b7bfafc65898ed2a': detectionStatistics,
    '4dc8f244b7bfafc65898ed2d': segmentationStatistics,
};
