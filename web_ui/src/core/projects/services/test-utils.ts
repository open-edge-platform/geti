// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { LabelItemEditionState, LabelItemType, LabelTreeItem } from '../../labels/label-tree-view.interface';
import { LabelsRelationType } from '../../labels/label.interface';
import { DatasetDTO, ProjectDTO } from '../dtos/project.interface';
import { KeypointTaskDTO, TASK_TYPE } from '../dtos/task.interface';

const DEFAULT_DATASETS_DTO: DatasetDTO[] = [
    {
        id: 'training-dataset',
        name: 'Training dataset',
        use_for_training: true,
        creation_time: '2022-07-22T20:09:22.576000+00:00',
    },
];

export const FLAT_LABELS: LabelTreeItem[] = [
    {
        ...getMockedLabel({ id: 'label', name: 'label', color: '#eeddbb' }),
        open: false,
        inEditMode: false,
        children: [],
        state: LabelItemEditionState.IDLE,
        relation: LabelsRelationType.SINGLE_SELECTION,
        type: LabelItemType.LABEL,
    },
    {
        ...getMockedLabel({ id: 'label2', name: 'label2', color: '#eeddbb' }),
        open: false,
        inEditMode: false,
        children: [],
        state: LabelItemEditionState.IDLE,
        relation: LabelsRelationType.SINGLE_SELECTION,
        type: LabelItemType.LABEL,
    },
];

export const HIERARCHY_LABELS: LabelTreeItem[] = [
    {
        ...getMockedLabel({
            id: 'label',
            name: 'label',
            color: '#eeddbb',
            group: 'Default group',
        }),
        open: false,
        inEditMode: false,
        state: LabelItemEditionState.IDLE,
        relation: LabelsRelationType.SINGLE_SELECTION,
        type: LabelItemType.LABEL,
        children: [
            {
                ...getMockedLabel({
                    id: 'label-child',
                    name: 'label child',
                    color: '#eeddbb',
                    group: 'Default group',
                    parentLabelId: 'label',
                    hotkey: 'ctrl+2',
                }),
                open: false,
                inEditMode: false,
                state: LabelItemEditionState.IDLE,
                relation: LabelsRelationType.SINGLE_SELECTION,
                type: LabelItemType.LABEL,
                children: [
                    {
                        ...getMockedLabel({
                            id: 'label-child-child',
                            name: 'label child child',
                            color: '#eeddbb',
                            group: 'Default group',
                            parentLabelId: 'label-child',
                            hotkey: 'ctrl+3',
                        }),
                        open: false,
                        children: [],
                        inEditMode: false,
                        state: LabelItemEditionState.IDLE,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                        type: LabelItemType.LABEL,
                    },
                ],
            },
            {
                ...getMockedLabel({
                    id: 'label-child2',
                    name: 'label child2',
                    color: '#eeddbb',
                    group: 'Default group',
                    parentLabelId: 'label',
                    hotkey: 'ctrl+4',
                }),
                open: false,
                children: [],
                inEditMode: false,
                state: LabelItemEditionState.IDLE,
                relation: LabelsRelationType.SINGLE_SELECTION,
                type: LabelItemType.LABEL,
            },
        ],
    },
];

const FLAT_LABELS_BODY = [
    {
        id: '1',
        name: 'label',
        group: 'Default group',
        color: '#eeddbb',
        parent_id: null,
        hotkey: 'ctrl+1',
        is_empty: false,
        is_anomalous: false,
        is_background: false,
    },
    {
        id: '2',
        name: 'label2',
        group: 'Default group',
        color: '#eeddbb',
        parent_id: null,
        hotkey: 'ctrl+2',
        is_empty: false,
        is_anomalous: false,
        is_background: false,
    },
];

export const PROJECT_DETECTION: ProjectDTO = {
    id: 'project-detection',
    creation_time: new Date().toISOString(),
    thumbnail: '',
    performance: {
        score: 0.65,
        task_performances: [
            {
                score: {
                    value: 0.65,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    name: 'test-project',
    pipeline: {
        connections: [
            {
                from: 'Dataset',
                to: 'Detection',
            },
        ],
        tasks: [
            {
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Image Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.DATASET,
                title: 'Detection',
                labels: FLAT_LABELS_BODY,
            },
        ],
    },
    datasets: DEFAULT_DATASETS_DTO,
    storage_info: {},
};

export const PROJECT_DETECTION_ORIENTED = {
    ...PROJECT_DETECTION,
    id: 'project-detection-oriented',
    pipeline: {
        ...PROJECT_DETECTION.pipeline,
        connections: [
            {
                from: 'Dataset',
                to: 'Detection oriented',
            },
        ],
    },
};

export const PROJECT_SEGMENTATION: ProjectDTO = {
    id: 'project-segmentation',
    creation_time: new Date().toISOString(),
    thumbnail: '',
    performance: {
        score: 0.65,
        task_performances: [
            {
                score: {
                    value: 0.65,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    name: 'test-project',
    pipeline: {
        connections: [
            {
                from: 'Dataset',
                to: 'Segmentation',
            },
        ],
        tasks: [
            {
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Image Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.DATASET,
                title: 'Segmentation',
                labels: FLAT_LABELS_BODY,
            },
        ],
    },
    datasets: DEFAULT_DATASETS_DTO,
    storage_info: {},
};

export const PROJECT_SEGMENTATION_INSTANCE = {
    ...PROJECT_SEGMENTATION,
    id: 'project-segmentation-instance',
    pipeline: {
        ...PROJECT_SEGMENTATION.pipeline,
        connections: [
            {
                from: 'Dataset',
                to: 'Segmentation instance',
            },
        ],
    },
};

const keypointTask: KeypointTaskDTO = {
    id: 'task2',
    task_type: TASK_TYPE.KEYPOINT_DETECTION,
    title: 'Keypoint detection',
    labels: FLAT_LABELS_BODY,
    keypoint_structure: { edges: [], positions: [] },
};

export const PROJECT_KEYPOINT_DETECTION: ProjectDTO = {
    id: 'project-keypoint-detection',
    creation_time: new Date().toISOString(),
    thumbnail: '',
    performance: {
        score: 0.65,
        task_performances: [
            {
                score: { value: 0.65, metric_type: 'accuracy' },
                task_id: 'task-id',
            },
        ],
    },
    name: 'test-project',
    pipeline: {
        connections: [
            {
                from: 'Dataset',
                to: 'Keypoint Detection',
            },
        ],
        tasks: [
            {
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Image Dataset',
            },
            keypointTask,
        ],
    },
    datasets: DEFAULT_DATASETS_DTO,
    storage_info: {},
};

const HIERARCHY_LABELS_BODY = [
    {
        id: 'label1',
        name: 'label',
        group: 'Default group',
        color: '#eeddbb',
        parent_id: null,
        hotkey: 'ctrl+1',
        is_empty: false,
        is_anomalous: false,
        is_background: false,
    },
    {
        id: 'label2',
        name: 'label child',
        group: 'Default group',
        color: '#eeddbb',
        parent_id: 'label',
        hotkey: 'ctrl+2',
        is_empty: false,
        is_anomalous: false,
        is_background: false,
    },
    {
        id: 'label3',
        name: 'label child child',
        group: 'Default group',
        color: '#eeddbb',
        parent_id: 'label child',
        hotkey: 'ctrl+3',
        is_empty: false,
        is_anomalous: false,
        is_background: false,
    },
    {
        id: 'label4',
        name: 'label child2',
        group: 'Default group',
        color: '#eeddbb',
        parent_id: 'label',
        hotkey: 'ctrl+4',
        is_empty: false,
        is_anomalous: false,
        is_background: false,
    },
];

export const PROJECT_CLASSIFICATION: ProjectDTO = {
    id: 'project-classification',
    creation_time: new Date().toISOString(),
    thumbnail: '',
    performance: {
        score: 0.69,
        task_performances: [
            {
                score: {
                    value: 0.69,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    name: 'test-project',
    pipeline: {
        connections: [
            {
                from: 'Dataset',
                to: 'Classification',
            },
        ],
        tasks: [
            {
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.CLASSIFICATION,
                title: 'Classification',
                labels: HIERARCHY_LABELS_BODY,
            },
        ],
    },
    datasets: DEFAULT_DATASETS_DTO,
    storage_info: {},
};

const PROJECT_ANOMALY: ProjectDTO = {
    id: 'project-anomaly',
    creation_time: new Date().toISOString(),
    thumbnail: '',
    performance: {
        score: 0.75,
        task_performances: [
            {
                score: {
                    value: 0.75,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    name: 'test-project',
    pipeline: {
        connections: [
            {
                from: 'Dataset',
                to: 'Anomaly',
            },
        ],
        tasks: [
            {
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.ANOMALY_CLASSIFICATION,
                title: 'Anomaly',
            },
        ],
    },
    datasets: DEFAULT_DATASETS_DTO,
    storage_info: {},
};

export const PROJECT_ANOMALY_CLASSIFICATION = {
    ...PROJECT_ANOMALY,
    pipeline: {
        ...PROJECT_ANOMALY.pipeline,
        connections: [
            {
                from: 'Dataset',
                to: 'Anomaly classification',
            },
        ],
    },
};

export const PROJECT_ANOMALY_DETECTION = {
    ...PROJECT_ANOMALY,
    pipeline: {
        ...PROJECT_ANOMALY.pipeline,
        connections: [
            {
                from: 'Dataset',
                to: 'Anomaly detection',
            },
        ],
        tasks: [
            {
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.ANOMALY_DETECTION,
                title: 'Anomaly',
            },
        ],
    },
};

export const PROJECT_ANOMALY_SEGMENTATION = {
    ...PROJECT_ANOMALY,
    pipeline: {
        ...PROJECT_ANOMALY.pipeline,
        connections: [
            {
                from: 'Dataset',
                to: 'Anomaly segmentation',
            },
        ],
        tasks: [
            {
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.ANOMALY_SEGMENTATION,
                title: 'Anomaly',
            },
        ],
    },
};

export const PROJECT_DETECTION_CLASSIFICATION: ProjectDTO = {
    id: 'project-detection-classification',
    creation_time: new Date().toISOString(),
    thumbnail: '',
    performance: {
        score: 0.9,
        task_performances: [
            {
                score: {
                    value: 0.9,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    name: 'test-project',
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
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.DETECTION,
                title: 'Detection',
                labels: FLAT_LABELS_BODY,
            },
            {
                id: 'task3',
                task_type: TASK_TYPE.CLASSIFICATION,
                title: 'Classification',
                labels: HIERARCHY_LABELS_BODY,
            },
        ],
    },
    datasets: DEFAULT_DATASETS_DTO,
    storage_info: {},
};

export const PROJECT_DETECTION_SEGMENTATION: ProjectDTO = {
    id: 'project-detection-segmentation',
    creation_time: new Date().toISOString(),
    thumbnail: '',
    performance: {
        score: 0.99,
        task_performances: [
            {
                score: {
                    value: 0.99,
                    metric_type: 'accuracy',
                },
                task_id: 'task-id',
            },
        ],
    },
    name: 'test-project',
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
                id: 'task1',
                task_type: TASK_TYPE.DATASET,
                title: 'Dataset',
            },
            {
                id: 'task2',
                task_type: TASK_TYPE.DETECTION,
                title: 'Detection',
                labels: FLAT_LABELS_BODY,
            },
            {
                id: 'task3',
                task_type: TASK_TYPE.SEGMENTATION,
                title: 'Segmentation',
                labels: FLAT_LABELS_BODY,
            },
        ],
    },
    datasets: DEFAULT_DATASETS_DTO,
    storage_info: {},
};

export const PROJECT_RESPONSE = (): ProjectDTO => {
    return {
        creation_time: '2021-06-01T10:20:16.209000+00:00',
        id: '60b609e0d036ba4566726c7f',
        name: 'Card detection',
        pipeline: {
            connections: [
                {
                    from: '60b609e0d036ba4566726c80',
                    to: '60b609e0d036ba4566726c81',
                },
            ],
            tasks: [
                {
                    task_type: TASK_TYPE.DATASET,
                    id: '60b609e0d036ba4566726c80',
                    labels: [],
                    title: 'Dataset',
                },
                {
                    task_type: TASK_TYPE.DETECTION,
                    id: '60b609e0d036ba4566726c81',
                    labels: [
                        {
                            color: '#fff5f7ff',
                            group: 'Label Group 1',
                            id: '60b609e0d036ba4566726c82',
                            name: 'card',
                            parent_id: null,
                            hotkey: 'ctrl+1',
                            is_empty: false,
                            is_anomalous: false,
                            is_background: false,
                        },
                    ],
                    title: 'Detection',
                },
            ],
        },
        performance: {
            score: 0.768,
            task_performances: [
                {
                    score: {
                        value: 0.768,
                        metric_type: 'accuracy',
                    },
                    task_id: '60b609e0d036ba4566726c81',
                },
            ],
        },
        thumbnail: '/v2/projects/60b609e0d036ba4566726c7f/thumbnail',
        datasets: DEFAULT_DATASETS_DTO,
        storage_info: {},
    };
};
