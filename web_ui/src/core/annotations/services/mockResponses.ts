// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Point } from '../../../core/annotations/shapes.interface';
import { getMockedLabel, labels as mockedLabelHierarchy } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { Label } from '../../labels/label.interface';
import { MEDIA_TYPE } from '../../media/base-media.interface';
import {
    AnnotationDTO,
    AnnotationResultDTO,
    KeypointAnnotationDTO,
    RectDTO,
    SHAPE_TYPE_DTO,
    VideoAnnotationsDTO,
} from '../dtos/annotation.interface';
import { ExplanationDTO, PredictionDTO, VideoPredictionsDTO } from '../dtos/prediction.interface';

const mockAnnotations: AnnotationDTO[] = [
    {
        id: 'd69b4403-4f4c-4e66-936e-b8565dd1a8a1',
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                probability: 1.0,
                source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                hotkey: '',
            },
        ],
        shape: {
            height: 16,
            type: SHAPE_TYPE_DTO.RECTANGLE,
            width: 19,
            x: 65,
            y: 31,
        },
        labels_to_revisit: [],
    },
    {
        id: '54af0335-5074-4024-a9dc-f04417ab1b1c',
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                probability: 1.0,
                source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                hotkey: '',
            },
        ],
        shape: {
            height: 30,
            type: SHAPE_TYPE_DTO.ELLIPSE,
            width: 30,
            x: 19,
            y: 1,
        },
        labels_to_revisit: [],
    },
    {
        id: 'ccfb81c6-a162-4f8f-b1c2-f97f51b0949d',
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                probability: 1.0,
                source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                hotkey: '',
            },
        ],
        shape: {
            points: [
                { x: 20, y: 20 },
                { x: 40, y: 20 },
                { x: 30, y: 30 },
            ],
            type: SHAPE_TYPE_DTO.POLYGON,
        },
        labels_to_revisit: [],
    },
    {
        id: '54af0335-5074-4024-a9dc-f04417ab1b1c',
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                probability: 1.0,
                source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                hotkey: '',
            },
        ],
        shape: {
            height: 40,
            type: SHAPE_TYPE_DTO.ELLIPSE,
            width: 30,
            x: 19,
            y: 1,
        },
        labels_to_revisit: [],
    },
];

const mockKeypointAnnotations: KeypointAnnotationDTO[] = [
    {
        id: 'test-1',
        shape: { type: SHAPE_TYPE_DTO.KEYPOINT, x: 0, y: 0, is_visible: true },
        labels_to_revisit: [],
        labels: [
            {
                id: '60b609e0d036ba4566726c82',
                hotkey: '',
                probability: 1.0,
                source: { user_id: 'default_user', model_id: null, model_storage_id: null },
            },
        ],
    },
    {
        id: 'test-2',
        shape: { type: SHAPE_TYPE_DTO.KEYPOINT, x: 10, y: 10, is_visible: true },
        labels_to_revisit: [],
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                hotkey: '',
                probability: 1.0,
                source: { user_id: 'default_user', model_id: null, model_storage_id: null },
            },
        ],
    },
];
const mockPredictionAnnotations: AnnotationDTO[] = [
    {
        id: 'd69b4403-4f4c-4e66-936e-b8565dd1a8a1',
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                probability: 1.0,
                source: { user_id: null, model_id: 'model-id', model_storage_id: 'model-storage-id' },
                hotkey: '',
            },
        ],
        shape: {
            height: 16,
            type: SHAPE_TYPE_DTO.RECTANGLE,
            width: 19,
            x: 65,
            y: 31,
        },
        labels_to_revisit: [],
    },
    {
        id: '54af0335-5074-4024-a9dc-f04417ab1b1c',
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                probability: 1.0,
                source: { user_id: null, model_id: 'model-id', model_storage_id: 'model-storage-id' },
                hotkey: '',
            },
        ],
        shape: {
            height: 30,
            type: SHAPE_TYPE_DTO.ELLIPSE,
            width: 30,
            x: 19,
            y: 1,
        },
        labels_to_revisit: [],
    },
    {
        id: 'ccfb81c6-a162-4f8f-b1c2-f97f51b0949d',
        labels: [
            {
                id: '60b6153817057389ba93f42e',
                probability: 1.0,
                source: { user_id: null, model_id: 'model-id', model_storage_id: 'model-storage-id' },
                hotkey: '',
            },
        ],
        shape: {
            points: [
                { x: 20, y: 20 },
                { x: 40, y: 20 },
                { x: 30, y: 30 },
            ],
            type: SHAPE_TYPE_DTO.POLYGON,
        },
        labels_to_revisit: [],
    },
];

const mockMapRoi = {
    id: '123',
    shape: {
        y: 0,
        x: 0,
        type: 'RECTANGLE',
        height: 0,
        width: 0,
    },
};

const mockExplanations: ExplanationDTO[] = [
    {
        id: '6138bca43b7b11505c43f2c1',
        label_id: '6138bca43b7b11505c43f2c1',
        name: 'Lorem',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/600/400',
    },
    {
        id: '6138bca43b7b11505c43f2c2',
        label_id: '6138bca43b7b11505c43f2c2',
        name: 'Ipsum',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/700/500',
    },
    {
        id: '6138bca43b7b11505c43f2c3',
        label_id: '6138bca43b7b11505c43f2c3',
        name: 'Dolor',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/800/600',
    },
    {
        id: '6138bca43b7b11505c43f2c4',
        label_id: '6138bca43b7b11505c43f2c4',
        name: 'Sit',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/900/700',
    },
    {
        id: '6138bca43b7b11505c43f2c5',
        label_id: '6138bca43b7b11505c43f2c5',
        name: 'Amet',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/1000/800',
    },
];

export const predictionsResponse = (): PredictionDTO => {
    return {
        annotations: mockPredictionAnnotations,
        maps: mockExplanations,
        id: '12312321',
        kind: 'prediction',
        media_identifier: {
            image_id: '60b609fbd036ba4566726c96',
            type: MEDIA_TYPE.IMAGE,
        },
        modified: '2021-06-03T13:09:18.096000+00:00',
    };
};

export const mockedInferencePrediction = ({ id = '123', name = 'label-test', probability = 0.1 }) => ({
    labels: [{ id, name, probability }],
    shape: {
        type: SHAPE_TYPE_DTO.RECTANGLE,
        x: 0,
        y: 0,
        height: 100,
        width: 100,
    },
});

export const mockedKeypointInferencePrediction = ({
    labels,
    probability,
}: {
    labels: Label[];
    probability: number;
}) => {
    return labels.map((label, index) => {
        return {
            labels: [{ ...label, probability }],
            shape: {
                is_visible: true,
                type: 'KEYPOINT',
                x: index + 1,
                y: index + 2,
            },
        };
    });
};

export const mockedExplanation = ({ labelId = '123', labelName = 'label-test' }) => ({
    maps: [
        {
            data: 'image-data',
            label_id: labelId,
            label_name: labelName,
        },
    ],
    created: '2023-11-29 10:35:40.697605677 +0000',
    media_identifier: {
        image_id: '6565f60508bf65b92817b530',
        type: 'image',
    },
});

export const mockedInferencePolygonPrediction = ({
    id = '123',
    name = 'label-test',
    probability = 0.1,
    points = [],
}: {
    id?: string;
    name?: string;
    probability?: number;
    points?: Point[];
}) => ({
    labels: [{ id, name, probability }],
    shape: { points, type: SHAPE_TYPE_DTO.POLYGON },
});

export const predictionsWithHierarchyResponse = (): PredictionDTO => {
    return {
        annotations: [
            {
                id: 'd69b4403-4f4c-4e66-936e-b8565dd1a8a1',
                labels: [
                    {
                        id: mockedLabelHierarchy[1].id,
                        probability: 1.0,
                        source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                        hotkey: '',
                    },
                    {
                        id: mockedLabelHierarchy[5].id,
                        probability: 1.0,
                        source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                        hotkey: '',
                    },
                    {
                        id: mockedLabelHierarchy[0].id,
                        probability: 1.0,
                        source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                        hotkey: '',
                    },
                    {
                        id: mockedLabelHierarchy[8].id,
                        probability: 1.0,
                        source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                        hotkey: '',
                    },
                ],
                shape: {
                    height: 0.16,
                    type: SHAPE_TYPE_DTO.RECTANGLE,
                    width: 0.19,
                    x: 0.65,
                    y: 0.31,
                },
                labels_to_revisit: [],
            },
        ],
        maps: mockExplanations,
        id: '12312321',
        kind: 'prediction',
        media_identifier: {
            image_id: '60b609fbd036ba4566726c96',
            type: MEDIA_TYPE.IMAGE,
        },
        modified: '2021-06-03T13:09:18.096000+00:00',
    };
};

export const imageAnnotationsResponse = (): AnnotationResultDTO => {
    return {
        annotations: mockAnnotations,
        id: 12312321,
        kind: 'annotation',
        media_identifier: {
            image_id: '60b609fbd036ba4566726c96',
            type: MEDIA_TYPE.IMAGE,
        },
        modified: '2021-06-03T13:09:18.096000+00:00',
        labels_to_revisit_full_scene: [],
        annotation_state_per_task: [],
    };
};

export const imageKeypointAnnotationsResponse = (): AnnotationResultDTO => {
    return {
        ...imageAnnotationsResponse(),
        annotations: mockKeypointAnnotations,
    };
};

export const videoAnnotationsResponse = (): VideoAnnotationsDTO => {
    return {
        video_annotations: [
            {
                annotations: mockAnnotations,
                id: '676575675',
                kind: 'annotation',
                media_identifier: {
                    frame_index: 1,
                    type: MEDIA_TYPE.VIDEO_FRAME,
                    video_id: '60b609fbd036ba4566726c96',
                },
                modified: '2021-06-03T13:09:18.096000+00:00',
                labels_to_revisit_full_scene: [],
            },
        ],
        video_annotation_properties: {
            end_frame: 100,
            requested_end_frame: 100,
            requested_start_frame: 0,
            start_frame: 0,
            total_count: 100,
            total_requested_count: 100,
        },
    };
};

export const videoPredictionsResponse = (): VideoPredictionsDTO => {
    return {
        video_predictions: [
            {
                annotations: mockAnnotations,
                id: '676575675',
                kind: 'prediction',
                media_identifier: {
                    frame_index: 1,
                    type: MEDIA_TYPE.VIDEO_FRAME,
                    video_id: '60b609fbd036ba4566726c96',
                },
                modified: '2021-06-03T13:09:18.096000+00:00',
                labels_to_revisit_full_scene: [],
            },
        ],
        video_prediction_properties: {
            end_frame: 100,
            requested_end_frame: 100,
            requested_start_frame: 0,
            start_frame: 0,
            total_count: 100,
            total_requested_count: 100,
        },
    };
};

export const mockedBatchPredictionShape = {
    height: 10,
    type: SHAPE_TYPE_DTO.RECTANGLE,
    width: 10,
    x: 0,
    y: 0,
} as RectDTO;

export const mockedBatchPrediction = (label: Label, probability = 1) => ({
    labels: [{ id: label.id, name: label.name, probability }],
    shape: mockedBatchPredictionShape,
});

export const getBatchPredictionsResponse = (label = getMockedLabel({})) => ({
    batch_predictions: [
        {
            predictions: [mockedBatchPrediction(label, 0.1)],
            created: '2023-12-11 15:00:11.33282577 +0000',
            media_identifier: {
                video_id: '6571cdbdb88021b61210da24',
                frame_index: 0,
                type: 'video_frame',
            },
        },
        {
            predictions: [mockedBatchPrediction(label, 0.2)],
            created: '2023-12-11 15:00:11.33282577 +0000',
            media_identifier: {
                video_id: '6571cdbdb88021b61210da24',
                frame_index: 10,
                type: 'video_frame',
            },
        },
    ],
});
