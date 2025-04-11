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

import { ShapeType } from '../../../core/annotations/shapetype.enum';
import { labelFromModel } from '../../../core/annotations/utils';
import { getMockedAnnotation } from '../../../test-utils/mocked-items-factory/mocked-annotations';
import { labels as mockedLabels } from '../../../test-utils/mocked-items-factory/mocked-labels';
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
});
