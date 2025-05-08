// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ImageIdDTO, SHAPE_TYPE_DTO } from '../../../core/annotations/dtos/annotation.interface';
import { NewPredictionsDTO } from '../../../core/annotations/dtos/prediction.interface';
import { convertPredictionsDTO, formatKeypointToAnnotationDTO } from '../../../core/annotations/services/utils';
import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { labelFromModel, labelFromUser } from '../../../core/annotations/utils';
import { getMockedAnnotation } from '../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels as mockedLabels } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { ToolPerAnnotation } from '../providers/analytics-annotation-scene-provider/use-enhanced-analytics-annotation-scene.hook';
import {
    getNumberOfNotEqualLabels,
    getNumberOfNotEqualShapes,
    getToolFrequencyUsage,
    getUniqueModelIds,
} from './utils';

describe('Analytics hooks utils', () => {
    describe('getUniqueModelIds', () => {
        it("should return only one model id if the predictions' labels have the same model id", () => {
            const modelId = 'model-id';
            const predictions = [
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation',
                        labels: [labelFromModel(mockedLabels[0], 0.8, modelId, '321')],
                    },
                    ShapeType.Rect
                ),
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation-2',
                        labels: [labelFromModel(mockedLabels[1], 0.8, modelId, '321')],
                    },
                    ShapeType.Rect
                ),
            ];

            expect(getUniqueModelIds(predictions)).toEqual([modelId]);
        });

        it("should return only all unique model ids if the predictions' labels have different model id", () => {
            const modelsIds = ['model-id-1', 'model-id-2', 'model-id-3'];
            const [modelIdForFirstAnnotation, modelIdForSecondAnnotation, modelIdForThirdAnnotation] = modelsIds;

            const predictions = [
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation',
                        labels: [labelFromModel(mockedLabels[0], 0.8, modelIdForFirstAnnotation, '321')],
                    },
                    ShapeType.Rect
                ),
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation-2',
                        labels: [labelFromModel(mockedLabels[1], 0.8, modelIdForSecondAnnotation, '321')],
                    },
                    ShapeType.Rect
                ),
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation-2',
                        labels: [labelFromModel(mockedLabels[1], 0.8, modelIdForThirdAnnotation, '321')],
                    },
                    ShapeType.Rect
                ),
            ];

            expect(getUniqueModelIds(predictions)).toEqual(modelsIds);
        });
    });

    describe('getNumberOfNotEqualShapes', () => {
        const annotationWithExactShape = getMockedAnnotation(
            {
                id: 'test-prediction-annotation-1',
                shape: {
                    shapeType: ShapeType.Rect,
                    x: 0,
                    y: 0,
                    height: 100,
                    width: 100,
                },
                labels: [labelFromModel(mockedLabels[0], 0.8, '123', '321')],
            },
            ShapeType.Rect
        );

        it('should return 0 as number of not equal shapes', () => {
            expect(getNumberOfNotEqualShapes([annotationWithExactShape], [annotationWithExactShape])).toBe(0);
        });

        it('should return 2 as number of not equal shapes', () => {
            const annotations = [
                annotationWithExactShape,
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation-2',
                        shape: {
                            shapeType: ShapeType.Rect,
                            x: 30,
                            y: 20,
                            height: 300,
                            width: 250,
                        },
                        labels: [labelFromModel(mockedLabels[1], 0.8, '123', '321')],
                    },
                    ShapeType.Rect
                ),
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation-3',
                        shape: {
                            shapeType: ShapeType.Rect,
                            x: 10,
                            y: 20,
                            height: 110,
                            width: 150,
                        },
                        labels: [labelFromModel(mockedLabels[1], 0.8, '123', '321')],
                    },
                    ShapeType.Rect
                ),
            ];

            const predictions = [
                annotationWithExactShape,
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation-2',
                        shape: {
                            shapeType: ShapeType.Rect,
                            x: 50,
                            y: 20,
                            height: 300,
                            width: 250,
                        },
                        labels: [labelFromModel(mockedLabels[1], 0.8, '123', '321')],
                    },
                    ShapeType.Rect
                ),
                getMockedAnnotation(
                    {
                        id: 'test-prediction-annotation-3',
                        shape: {
                            shapeType: ShapeType.Rect,
                            x: 10,
                            y: 20,
                            height: 120,
                            width: 150,
                        },
                        labels: [labelFromModel(mockedLabels[1], 0.8, '123', '321')],
                    },
                    ShapeType.Rect
                ),
            ];

            expect(getNumberOfNotEqualShapes(predictions, annotations)).toBe(2);
        });

        describe('getNumberOfNotEqualLabels', () => {
            const annotationWithExactLabel = getMockedAnnotation(
                {
                    id: 'test-prediction-annotation-1',
                    shape: {
                        shapeType: ShapeType.Rect,
                        x: 0,
                        y: 0,
                        height: 100,
                        width: 100,
                    },
                    labels: [labelFromModel(mockedLabels[0], 0.8, '123', '321')],
                },
                ShapeType.Rect
            );

            it('should return 0 as number of not equal labels', () => {
                expect(getNumberOfNotEqualLabels([annotationWithExactLabel], [annotationWithExactLabel])).toBe(0);
            });

            it('should return 2 as number of not equal labels', () => {
                const annotations = [
                    annotationWithExactLabel,
                    getMockedAnnotation(
                        {
                            id: 'test-prediction-annotation-2',
                            shape: {
                                shapeType: ShapeType.Rect,
                                x: 0,
                                y: 0,
                                height: 100,
                                width: 100,
                            },
                            labels: [labelFromModel(mockedLabels[0], 0.8, '123', '321')],
                        },
                        ShapeType.Rect
                    ),
                    getMockedAnnotation(
                        {
                            id: 'test-prediction-annotation-3',
                            shape: {
                                shapeType: ShapeType.Rect,
                                x: 0,
                                y: 0,
                                height: 100,
                                width: 100,
                            },
                            labels: [labelFromModel(mockedLabels[1], 0.8, '123', '321')],
                        },
                        ShapeType.Rect
                    ),
                ];

                const predictions = [
                    annotationWithExactLabel,
                    getMockedAnnotation(
                        {
                            id: 'test-prediction-annotation-2',
                            shape: {
                                shapeType: ShapeType.Rect,
                                x: 0,
                                y: 0,
                                height: 100,
                                width: 100,
                            },
                            labels: [labelFromModel(mockedLabels[1], 0.8, '123', '321')],
                        },
                        ShapeType.Rect
                    ),
                    getMockedAnnotation(
                        {
                            id: 'test-prediction-annotation-3',
                            shape: {
                                shapeType: ShapeType.Rect,
                                x: 0,
                                y: 0,
                                height: 100,
                                width: 100,
                            },
                            labels: [labelFromModel(mockedLabels[0], 0.8, '123', '321')],
                        },
                        ShapeType.Rect
                    ),
                ];

                expect(getNumberOfNotEqualLabels(predictions, annotations)).toBe(2);
            });
        });
    });

    describe('getToolFrequencyUsage', () => {
        const boundingBoxTool = 'Bounding box';
        const circleTool = 'Circle';
        const ssimTool = 'Detection assistant';

        const toolPerAnnotation: ToolPerAnnotation = {
            'annotation-id-1': boundingBoxTool,
            'annotation-id-2': boundingBoxTool,
            'annotation-id-3': boundingBoxTool,
            'annotation-id-4': circleTool,
            'annotation-id-5': ssimTool,
            'annotation-id-6': ssimTool,
            'annotation-id-7': ssimTool,
            'annotation-id-8': ssimTool,
            'annotation-id-9': ssimTool,
        };

        it('should return frequency per tool type', () => {
            expect(getToolFrequencyUsage(toolPerAnnotation)).toEqual({
                [boundingBoxTool]: 3,
                [circleTool]: 1,
                [ssimTool]: 5,
            });
        });
    });

    it('formatKeypointToAnnotationDTO', () => {
        const mockedTime = '2023-01-01T00:00:00Z';
        const mockedKeypointPrediction = { id: 'keypoint-id', name: 'keypoint-name', score: 0.85, x: 100, y: 200 };

        expect(formatKeypointToAnnotationDTO(mockedTime)(mockedKeypointPrediction)).toEqual(
            expect.objectContaining({
                shape: {
                    x: mockedKeypointPrediction.x,
                    y: mockedKeypointPrediction.y,
                    is_visible: true,
                    type: SHAPE_TYPE_DTO.KEYPOINT,
                },
                labels: [
                    {
                        id: 'keypoint-id',
                        probability: mockedKeypointPrediction.score,
                        source: {
                            model_id: 'latest',
                            user_id: null,
                            model_storage_id: 'storage_id',
                        },
                    },
                ],
                labels_to_revisit: [],
                modified: mockedTime,
            })
        );
    });
});
describe('convertPredictionsDTO', () => {
    const mockMediaId = { image_id: 'test-image-id', type: 'image' } as ImageIdDTO;
    const mockTimeCreated = '2023-01-01T12:00:00Z';

    it('convert regular predictions', () => {
        const mockNewPredictions: NewPredictionsDTO = {
            created: mockTimeCreated,
            predictions: [
                {
                    shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 10, y: 20, width: 100, height: 150 },
                    labels: [{ id: 'label-1', name: 'person', probability: 0.9 }],
                },
            ],
        };

        const result = convertPredictionsDTO(mockNewPredictions, mockMediaId);

        expect(result).toEqual(
            expect.objectContaining({
                kind: 'prediction',
                maps: [],
                media_identifier: mockMediaId,
                modified: mockTimeCreated,
                annotations: expect.arrayContaining([
                    expect.objectContaining({
                        labels: [
                            expect.objectContaining({
                                id: 'label-1',
                                probability: 0.9,
                                source: { model_id: 'latest', user_id: null, model_storage_id: 'storage_id' },
                            }),
                        ],
                        shape: mockNewPredictions.predictions[0].shape,
                        labels_to_revisit: [],
                        modified: mockTimeCreated,
                    }),
                ]),
            })
        );
    });

    /*  it('should convert keypoint predictions correctly', () => {
        const mockNewPredictions: NewPredictionsDTO = {
            created: mockTimeCreated,
            predictions: [
                {
                    keypoints: [{ id: 'kp-2', name: 'left_eye', score: 0.85, x: 120, y: 130 }],
                    created: '',
                },
            ],
        };

        const result = convertPredictionsDTO(mockNewPredictions, mockMediaId);

        expect(result).toEqual(
            expect.objectContaining({
                kind: 'prediction',
                maps: [],
                media_identifier: mockMediaId,
                modified: mockTimeCreated,
            })
        );

        // Verify each keypoint is converted correctly
        const keypointData = [{ id: 'kp-2', name: 'left_eye', score: 0.85, x: 120, y: 130 }];
        keypointData.forEach((kp, index) => {
            // Verify each keypoint is converted correctly
            keypointData.forEach((kp, index) => {
                expect(result.annotations[index]).toEqual(
                    expect.objectContaining({
                        shape: {
                            x: kp.x,
                            y: kp.y,
                            is_visible: true,
                            type: SHAPE_TYPE_DTO.KEYPOINT,
                        },
                        labels: [
                            expect.objectContaining({
                                id: kp.id,
                                probability: kp.score,
                            }),
                        ],
                        labels_to_revisit: [],
                        modified: mockTimeCreated,
                    })
                );
            });
        });
    }); */
});
