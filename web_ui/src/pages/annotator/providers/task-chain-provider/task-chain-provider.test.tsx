// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { getIds } from '@shared/utils';
import { act, renderHook } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { Label, LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { Task } from '../../../../core/projects/task.interface';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels as mockedLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import {
    AnnotationSceneProvider,
    useAnnotationScene,
} from '../annotation-scene-provider/annotation-scene-provider.component';
import { TaskChainProvider } from './task-chain-provider.component';

const IMAGE_WIDTH = 200;
const IMAGE_HEIGHT = 200;
const EMPTY_SHAPE = { shapeType: ShapeType.Rect as const, x: 0, y: 0, width: IMAGE_WIDTH, height: IMAGE_HEIGHT };

// Used to mock the image ROI
jest.mock('../selected-media-item-provider/selected-media-item-provider.component', () => ({
    useSelectedMediaItem: () => {
        return {
            selectedMediaItem: {
                image: { x: 0, y: 0, width: IMAGE_WIDTH, height: IMAGE_HEIGHT },
            },
        };
    },
}));

const wrapper = ({
    children,
    annotations,
    tasks,
    selectedTask = tasks[0],
}: {
    children?: ReactNode;
    tasks: Task[];
    selectedTask?: Task | null;
    annotations: Annotation[];
}) => {
    const labels = tasks.flatMap((task) => task.labels);
    return (
        <AnnotationSceneProvider annotations={annotations} labels={labels}>
            <TaskChainProvider tasks={tasks} selectedTask={selectedTask} defaultLabel={null}>
                {children}
            </TaskChainProvider>
        </AnnotationSceneProvider>
    );
};

const renderAnnotationSceneHook = (props: { tasks: Task[]; selectedTask?: Task | null; annotations: Annotation[] }) => {
    return renderHook(() => useAnnotationScene(), {
        wrapper: ({ children }) => wrapper({ children, ...props }),
    });
};

describe('TaskChainProvider', (): void => {
    const emptyDetectionLabel = getMockedLabel({
        id: 'empty-detection-id',
        isExclusive: true,
        group: 'empty-detection-group',
    });
    const detectionLabels = [getMockedLabel({ id: '1' }), emptyDetectionLabel];

    const emptySegmentationLabel = getMockedLabel({
        id: 'empty-segmentation-id',
        isExclusive: true,
        group: 'empty-segmentation-group',
    });
    const segmentationLabels = [getMockedLabel({ id: '2' }), emptySegmentationLabel];

    const tasks = [
        getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: detectionLabels }),
        getMockedTask({ id: '2', domain: DOMAIN.SEGMENTATION, labels: segmentationLabels }),
    ];

    it('uses the annotation scene', () => {
        const annotations = [
            getMockedAnnotation({ id: '1', labels: [] }),
            getMockedAnnotation({ id: '2', labels: [labelFromUser(detectionLabels[0])] }),
            getMockedAnnotation({ id: '3', labels: [labelFromUser(detectionLabels[0])], isSelected: true }),
            getMockedAnnotation({
                id: '4',
                labels: [labelFromUser(segmentationLabels[0])],
                isSelected: true,
            }),
            getMockedAnnotation({
                id: '5',
                labels: [labelFromUser(segmentationLabels[0])],
            }),
        ];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

        expect(result.current.annotations.filter(({ isSelected }) => isSelected)).toHaveLength(2);
        expect(result.current.annotations[2].isSelected).toBe(true);
        expect(result.current.annotations[3].isSelected).toBe(true);
    });

    it('selects the last added input for a task', () => {
        const annotations = [
            getMockedAnnotation({ id: '1', labels: [] }),
            getMockedAnnotation({ id: '2', labels: [labelFromUser(detectionLabels[0])] }),
            getMockedAnnotation({ id: '3', labels: [labelFromUser(detectionLabels[0])] }),
            getMockedAnnotation({ id: '4', labels: [labelFromUser(segmentationLabels[0])], isSelected: true }),
            getMockedAnnotation({ id: '5', labels: [labelFromUser(segmentationLabels[0])] }),
        ];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

        expect(result.current.annotations.filter(({ isSelected }) => isSelected)).toHaveLength(2);
        expect(result.current.annotations[2].isSelected).toBe(true);
        expect(result.current.annotations[3].isSelected).toBe(true);
    });

    it("selects the task's selected input and the new annotation after drawing", () => {
        const annotations = [
            getMockedAnnotation({ id: '1', labels: [] }),
            getMockedAnnotation({ id: '2', labels: [labelFromUser(detectionLabels[0])], isSelected: true }),
            getMockedAnnotation({ id: '3', labels: [labelFromUser(detectionLabels[0])] }),
            getMockedAnnotation({ id: '4', labels: [labelFromUser(segmentationLabels[0])], isSelected: true }),
            getMockedAnnotation({ id: '5', labels: [labelFromUser(segmentationLabels[0])] }),
        ];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

        act(() => {
            result.current.addShapes(
                [{ shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 }],
                [segmentationLabels[0]]
            );
        });

        expect(result.current.annotations.filter(({ isSelected }) => isSelected)).toHaveLength(2);
        expect(result.current.annotations[1].isSelected).toBe(true);
        expect(result.current.annotations[3].isSelected).toBe(false);
        expect(result.current.annotations[5].isSelected).toBe(true);
    });

    describe('addAnnotations', () => {
        it('When using addAnnotations only the input remains selected', () => {
            const annotations = [
                getMockedAnnotation({ id: '1', labels: [] }),
                getMockedAnnotation({ id: '2', labels: [labelFromUser(detectionLabels[0])], isSelected: true }),
                getMockedAnnotation({ id: '3', labels: [labelFromUser(detectionLabels[0])] }),
                getMockedAnnotation({ id: '4', labels: [labelFromUser(segmentationLabels[0])], isSelected: true }),
                getMockedAnnotation({ id: '5', labels: [labelFromUser(segmentationLabels[0])] }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

            act(() => {
                result.current.addAnnotations([
                    getMockedAnnotation({ id: '6', labels: [labelFromUser(segmentationLabels[0])] }),
                ]);
            });

            expect(result.current.annotations.filter(({ isSelected }) => isSelected)).toHaveLength(1);
            expect(result.current.annotations[1].isSelected).toBe(true);
            expect(result.current.annotations[3].isSelected).toBe(false);
            expect(result.current.annotations[5].isSelected).toBe(false);
        });

        it('removes empty annotations', () => {
            const annotations = [
                getMockedAnnotation({ id: '1', labels: [labelFromUser(emptyDetectionLabel)], shape: EMPTY_SHAPE }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

            act(() => {
                result.current.addAnnotations([
                    getMockedAnnotation({ id: '2', labels: [labelFromUser(detectionLabels[0])] }),
                ]);
            });

            expect(result.current.annotations).toHaveLength(1);
            expect(result.current.annotations[0].id).toEqual('2');
        });

        it('detection -> segmentation, removes empty labels from detection annotations', () => {
            const annotations = [
                getMockedAnnotation({
                    id: '1',
                    labels: [labelFromUser(detectionLabels[0]), labelFromUser(emptySegmentationLabel)],
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 20, height: 20 },
                }),
                getMockedAnnotation({
                    id: '2',
                    labels: [labelFromUser(detectionLabels[0]), labelFromUser(emptySegmentationLabel)],
                    shape: { shapeType: ShapeType.Rect, x: 100, y: 100, width: 20, height: 20 },
                }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

            act(() => {
                result.current.addAnnotations([
                    getMockedAnnotation({
                        id: '3',
                        labels: [labelFromUser(segmentationLabels[0])],
                        shape: { shapeType: ShapeType.Rect, x: 15, y: 15, width: 10, height: 10 },
                    }),
                    getMockedAnnotation({
                        id: '4',
                        labels: [labelFromUser(segmentationLabels[0])],
                        shape: { shapeType: ShapeType.Rect, x: 105, y: 105, width: 10, height: 10 },
                    }),
                ]);
            });

            expect(result.current.annotations).toHaveLength(4);
            expect(result.current.annotations.filter(({ isSelected }) => isSelected)).toHaveLength(1);
            expect(result.current.annotations[0].labels).toHaveLength(1);
        });
    });

    describe('(un)Selecting annotations', () => {
        it('allows selecting at most 1 task input even when they were selected from a different task', () => {
            // annotations 2 and 3 were selected in all task, but only 3 is shown
            // to be selected in the segmentation task
            const annotations = [
                getMockedAnnotation({ id: '1', labels: [] }),
                getMockedAnnotation({ id: '2', labels: [labelFromUser(detectionLabels[0])], isSelected: true }),
                getMockedAnnotation({ id: '3', labels: [labelFromUser(detectionLabels[0])], isSelected: true }),
                getMockedAnnotation({ id: '4', labels: [labelFromUser(segmentationLabels[0])], isSelected: true }),
                getMockedAnnotation({ id: '5', labels: [labelFromUser(segmentationLabels[0])] }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

            expect(result.current.annotations[1].isSelected).toBe(false);
            expect(result.current.annotations[2].isSelected).toBe(true);
            expect(result.current.annotations[3].isSelected).toBe(true);
            expect(result.current.annotations[4].isSelected).toBe(false);
        });

        it('allows selecting at most 1 task input', () => {
            const annotations = [
                getMockedAnnotation({ id: '1', labels: [] }),
                getMockedAnnotation({ id: '2', labels: [labelFromUser(detectionLabels[0])], isSelected: true }),
                getMockedAnnotation({ id: '3', labels: [labelFromUser(detectionLabels[0])] }),
                getMockedAnnotation({ id: '4', labels: [labelFromUser(segmentationLabels[0])], isSelected: true }),
                getMockedAnnotation({ id: '5', labels: [labelFromUser(segmentationLabels[0])] }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask: tasks[1] });

            // Selecting multiple outputs is allowed
            act(() => {
                result.current.selectAnnotation(annotations[4].id);
            });
            expect(result.current.annotations[1].isSelected).toBe(true);
            expect(result.current.annotations[2].isSelected).toBe(false);
            expect(result.current.annotations[3].isSelected).toBe(true);
            expect(result.current.annotations[4].isSelected).toBe(true);

            // Selecting an input deselects the other input
            act(() => {
                result.current.selectAnnotation(annotations[2].id);
            });
            expect(result.current.annotations[1].isSelected).toBe(false);
            expect(result.current.annotations[2].isSelected).toBe(true);
            expect(result.current.annotations[3].isSelected).toBe(true);
            expect(result.current.annotations[4].isSelected).toBe(true);
        });
    });
});

describe('Empty labels', () => {
    describe('single task proejcts', () => {
        const emptyLabel = getMockedLabel({
            id: 'empty-id',
            isExclusive: true,
            group: 'empty-group',
        });
        const labels: Label[] = [...mockedLabels, emptyLabel];

        describe('classification (single global)', () => {
            const tasks = [getMockedTask({ id: '1', domain: DOMAIN.CLASSIFICATION, labels })];

            it('adds an empty label', () => {
                const annotations = [getMockedAnnotation({ id: '1', labels: [], isSelected: true })];
                const { result } = renderAnnotationSceneHook({ tasks, annotations });

                act(() => {
                    result.current.addLabel(emptyLabel, [result.current.annotations[0].id]);
                });

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0].labels).toEqual([labelFromUser(emptyLabel)]);
            });

            it('removes labels when assigning an empty label', () => {
                const annotations = [
                    getMockedAnnotation({
                        id: '1',
                        labels: [labelFromUser(labels[1]), labelFromUser(labels[3])],
                        isSelected: true,
                    }),
                ];
                const { result } = renderAnnotationSceneHook({ tasks, annotations });

                act(() => {
                    result.current.addLabel(emptyLabel, [result.current.annotations[0].id]);
                });

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0].labels).toEqual([labelFromUser(emptyLabel)]);
            });

            it('removes empty label when assigning a different label', () => {
                const annotations = [
                    getMockedAnnotation({
                        id: '1',
                        labels: [labelFromUser(emptyLabel)],
                        isSelected: true,
                    }),
                ];
                const { result } = renderAnnotationSceneHook({ tasks, annotations });

                act(() => {
                    result.current.addLabel(labels[0], [result.current.annotations[0].id]);
                });

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0].labels).toEqual([labelFromUser(labels[0])]);
            });
        });

        describe('detection (single local)', () => {
            const tasks = [getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels })];

            it('adds a new empty annotation shape', () => {
                const annotations: Annotation[] = [];
                const { result } = renderAnnotationSceneHook({ tasks, annotations });

                act(() => {
                    result.current.addLabel(emptyLabel, []);
                });

                const expectedAnnotation = {
                    shape: EMPTY_SHAPE,
                    labels: [labelFromUser(emptyLabel)],
                    isSelected: true,
                };

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
            });

            it('can not add an empty label to an existing annotation', () => {
                const annotations: Annotation[] = [getMockedAnnotation({ id: 'non-empty' })];
                const { result } = renderAnnotationSceneHook({ tasks, annotations });

                act(() => {
                    result.current.addLabel(emptyLabel, [annotations[0].id]);
                });

                const expectedAnnotation = {
                    shape: EMPTY_SHAPE,
                    labels: [labelFromUser(emptyLabel)],
                    isSelected: true,
                };

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
            });

            it('removes other annotations when assigning empty label', () => {
                const annotations: Annotation[] = [
                    getMockedAnnotation({ id: 'non-empty' }),
                    getMockedAnnotation({ id: 'non-empty-2' }),
                ];
                const { result } = renderAnnotationSceneHook({ tasks, annotations });

                act(() => {
                    result.current.addLabel(emptyLabel, [annotations[0].id]);
                });

                const expectedAnnotation = {
                    shape: EMPTY_SHAPE,
                    labels: [labelFromUser(emptyLabel)],
                    isSelected: true,
                };

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
            });

            it('removes the empty label when adding a new shape', () => {
                const annotations: Annotation[] = [
                    getMockedAnnotation({ id: 'empty', labels: [labelFromUser(emptyLabel)] }),
                ];
                const { result } = renderAnnotationSceneHook({ tasks, annotations });

                const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };
                act(() => {
                    result.current.addShapes([shape], [labels[0]]);
                });

                const expectedAnnotation = {
                    shape,
                    labels: [labelFromUser(labels[0])],
                    isSelected: true,
                };

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
            });
        });
    });

    describe('task chain projects', () => {
        describe('detection -> classification (local -> global)', () => {
            const emptyDetectionLabel = getMockedLabel({
                id: 'empty-detection-id',
                isExclusive: true,
                group: 'empty-detection-group',
            });
            const emptyClassificationLabel = getMockedLabel({
                id: 'empty-classificatino-id',
                isExclusive: true,
                group: 'empty-classification-group',
                parentLabelId: 'card',
            });

            const [detectionLabel, ...classificationLabels] = mockedLabels;

            const tasks = [
                getMockedTask({
                    id: 'detection',
                    domain: DOMAIN.DETECTION,
                    labels: [detectionLabel, emptyDetectionLabel],
                }),
                getMockedTask({
                    id: 'classification',
                    domain: DOMAIN.CLASSIFICATION,
                    labels: [...classificationLabels, emptyClassificationLabel],
                }),
            ];

            describe('detection', () => {
                const selectedTask = tasks[0];

                it('adds a new empty annotation shape', () => {
                    const annotations: Annotation[] = [];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, []);
                    });

                    const expectedAnnotation = {
                        shape: EMPTY_SHAPE,
                        labels: [labelFromUser(emptyDetectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes other annotations when assigning empty label', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({ id: 'non-empty' }),
                        getMockedAnnotation({ id: 'non-empty-2' }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, [annotations[0].id]);
                    });

                    const expectedAnnotation = {
                        shape: EMPTY_SHAPE,
                        labels: [labelFromUser(emptyDetectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes the empty label when adding a new shape', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({ id: 'empty', labels: [labelFromUser(emptyDetectionLabel)] }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape], [detectionLabel]);
                    });

                    const expectedAnnotation = {
                        shape,
                        labels: [labelFromUser(detectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });
            });

            describe('classification', () => {
                const selectedTask = tasks[1];

                it('assigns an empty label to a detection annotation', () => {
                    const annotations = [
                        getMockedAnnotation({ id: '1', labels: [labelFromUser(detectionLabel)], isSelected: true }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyClassificationLabel, [result.current.annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptyClassificationLabel),
                    ]);
                });

                it('assigns an empty label to a detection annotation without specifying the annotation', () => {
                    const annotations = [
                        getMockedAnnotation({ id: '1', labels: [labelFromUser(detectionLabel)], isSelected: true }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyClassificationLabel, []);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptyClassificationLabel),
                    ]);
                });

                it('removes labels when assigning an empty label', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [
                                labelFromUser(detectionLabel),
                                labelFromUser(classificationLabels[0]),
                                labelFromUser(classificationLabels[4]),
                            ],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyClassificationLabel, [result.current.annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptyClassificationLabel),
                    ]);
                });

                it('removes empty label when assigning a different label', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [labelFromUser(detectionLabel), labelFromUser(emptyClassificationLabel)],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(classificationLabels[4], [result.current.annotations[0].id]);
                    });

                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(classificationLabels[0]),
                        labelFromUser(classificationLabels[4]),
                    ]);
                });

                it('does not allow adding an empty classification label without annotations', () => {
                    const { result } = renderAnnotationSceneHook({ tasks, annotations: [], selectedTask });

                    act(() => {
                        result.current.addLabel(emptyClassificationLabel, []);
                    });

                    expect(result.current.annotations).toHaveLength(0);
                });
            });

            describe('all tasks', () => {
                const selectedTask = null;

                // empty detection label
                it('adds a new empty annotation shape', () => {
                    const annotations: Annotation[] = [];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, []);
                    });

                    const expectedAnnotation = {
                        shape: EMPTY_SHAPE,
                        labels: [labelFromUser(emptyDetectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes other annotations when assigning empty label', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({ id: 'non-empty' }),
                        getMockedAnnotation({ id: 'non-empty-2' }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, [annotations[0].id]);
                    });

                    const expectedAnnotation = {
                        shape: EMPTY_SHAPE,
                        labels: [labelFromUser(emptyDetectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes the empty label when adding a new shape', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({ id: 'empty', labels: [labelFromUser(emptyDetectionLabel)] }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations });

                    const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape], [detectionLabel]);
                    });

                    const expectedAnnotation = {
                        shape,
                        labels: [labelFromUser(detectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                // empty classification label
                it('sets an empty classifiation label to a detection annotation', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyClassificationLabel, [annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptyClassificationLabel),
                    ]);
                });

                it('does not allow adding an empty classification label without input', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyClassificationLabel, []);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations).toEqual(annotations);
                });

                it('adds a shape with an empty label', () => {
                    const annotations: Annotation[] = [];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };

                    act(() => {
                        result.current.addShapes([shape], [emptyClassificationLabel]);
                    });

                    const expectedAnnotation = {
                        shape,
                        labels: [labelFromUser(detectionLabel), labelFromUser(emptyClassificationLabel)],
                        isSelected: true,
                    };
                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });
            });
        });

        describe('detection -> segmentation (local -> global)', () => {
            const emptyDetectionLabel = getMockedLabel({
                id: 'empty-detection-id',
                isExclusive: true,
                group: 'empty-detection-group',
            });
            const emptySegmentationLabel = getMockedLabel({
                id: 'empty-segmentation-id',
                isExclusive: true,
                group: 'empty-segmentation-group',
            });

            const detectionLabel = mockedLabels[0];
            const segmentationLabels = [
                { ...mockedLabels[1], parentLabelId: null },
                { ...mockedLabels[2], parentLabelId: null },
            ];

            const tasks = [
                getMockedTask({
                    id: 'detection',
                    domain: DOMAIN.DETECTION,
                    labels: [detectionLabel, emptyDetectionLabel],
                }),
                getMockedTask({
                    id: 'segmentation',
                    domain: DOMAIN.SEGMENTATION,
                    labels: [...segmentationLabels, emptySegmentationLabel],
                }),
            ];

            describe('detection', () => {
                const selectedTask = tasks[0];

                it('adds a new empty annotation shape', () => {
                    const annotations: Annotation[] = [];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, []);
                    });

                    const expectedAnnotation = {
                        shape: EMPTY_SHAPE,
                        labels: [labelFromUser(emptyDetectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes other annotations when assigning empty label', () => {
                    const annotations: Annotation[] = [
                        // Detection annotation with 2 segmentation annotations
                        getMockedAnnotation({
                            id: 'det-1',
                            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-2',
                            shape: { shapeType: ShapeType.Rect, x: 20, y: 20, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                        // Detection annotation with 1 segmentation annotation
                        getMockedAnnotation({
                            id: 'det-2',
                            shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-2-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 170, y: 170, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, [annotations[0].id]);
                    });

                    const expectedAnnotation = {
                        shape: EMPTY_SHAPE,
                        labels: [labelFromUser(emptyDetectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes the empty label when adding a new shape', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({ id: 'empty', labels: [labelFromUser(emptyDetectionLabel)] }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape], [detectionLabel]);
                    });

                    const expectedAnnotation = {
                        shape,
                        labels: [labelFromUser(detectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });
            });

            describe('segmentation', () => {
                const selectedTask = tasks[1];

                it('assigns an empty label to a detection annotation', () => {
                    const annotations = [
                        getMockedAnnotation({ id: '1', labels: [labelFromUser(detectionLabel)], isSelected: true }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, [result.current.annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptySegmentationLabel),
                    ]);
                });

                it('removes labels when assigning an empty label', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [labelFromUser(detectionLabel), labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, [result.current.annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptySegmentationLabel),
                    ]);
                });

                it('removes empty label when assigning a different label', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [labelFromUser(detectionLabel), labelFromUser(emptySegmentationLabel)],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(segmentationLabels[0], [result.current.annotations[0].id]);
                    });

                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(segmentationLabels[0]),
                    ]);
                });

                it('assigns an empty label to a detection annotation without specifying the annotation', () => {
                    const annotations = [
                        getMockedAnnotation({ id: '1', labels: [labelFromUser(detectionLabel)], isSelected: true }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, []);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptySegmentationLabel),
                    ]);
                });

                it('assigns an empty label to a detection annotation without specifying a selected annotation', () => {
                    // We implicitly select the input annotation
                    const annotations = [getMockedAnnotation({ id: '1', labels: [labelFromUser(detectionLabel)] })];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });
                    expect(result.current.annotations[0].isSelected).toEqual(true);

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, []);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptySegmentationLabel),
                    ]);
                });

                it('removes other annotations when assigning empty label', () => {
                    const annotations: Annotation[] = [
                        // Detection annotation with 2 segmentation annotations
                        getMockedAnnotation({
                            id: 'det-1',
                            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: false,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: false,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-2',
                            shape: { shapeType: ShapeType.Rect, x: 20, y: 20, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: false,
                        }),
                        // Detection annotation with 1 segmentation annotation
                        getMockedAnnotation({
                            id: 'det-2',
                            shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-2-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 170, y: 170, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: false,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, []);
                    });

                    const expectedAnnotation = {
                        id: 'det-2',
                        shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                        labels: [labelFromUser(detectionLabel), labelFromUser(emptySegmentationLabel)],
                    };

                    expect(result.current.annotations).toHaveLength(4);
                    expect(result.current.annotations[3]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes the empty label when adding a new shape', () => {
                    const annotations: Annotation[] = [
                        // Detection with empty segmentation
                        getMockedAnnotation({
                            id: 'det-1',
                            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                            labels: [labelFromUser(detectionLabel), labelFromUser(emptySegmentationLabel)],
                            isSelected: true,
                        }),
                        // Detection annotation with 1 segmentation annotation
                        getMockedAnnotation({
                            id: 'det-2',
                            shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: false,
                        }),
                        getMockedAnnotation({
                            id: 'det-2-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 170, y: 170, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: false,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape], [segmentationLabels[0]]);
                    });

                    expect(result.current.annotations).toHaveLength(4);
                    expect(result.current.annotations[0].labels).toEqual([labelFromUser(detectionLabel)]);
                });

                it('does not allow adding an empty segmentation label without annotations', () => {
                    const { result } = renderAnnotationSceneHook({ tasks, annotations: [], selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, []);
                    });

                    expect(result.current.annotations).toHaveLength(0);
                });
            });

            describe('all tasks', () => {
                const selectedTask = null;

                // empty detection label
                it('adds a new empty annotation shape', () => {
                    const annotations: Annotation[] = [];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, []);
                    });

                    const expectedAnnotation = {
                        shape: EMPTY_SHAPE,
                        labels: [labelFromUser(emptyDetectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes other detection annotations when assigning empty label', () => {
                    const annotations = [
                        // Detection annotation with 2 segmentation annotations
                        getMockedAnnotation({
                            id: 'det-1',
                            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-2',
                            shape: { shapeType: ShapeType.Rect, x: 20, y: 20, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                        // Detection annotation with 1 segmentation annotation
                        getMockedAnnotation({
                            id: 'det-2',
                            shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-2-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 170, y: 170, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptyDetectionLabel, [annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([labelFromUser(emptyDetectionLabel)]);
                    expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
                });

                it('removes the empty label when adding a detection annotation', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({
                            id: 'empty',
                            labels: [labelFromUser(emptyDetectionLabel)],
                            shape: EMPTY_SHAPE,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape], [detectionLabel]);
                    });

                    const expectedAnnotation = {
                        shape,
                        labels: [labelFromUser(detectionLabel)],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes the empty label when adding an annotation without label', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({
                            id: 'empty',
                            labels: [labelFromUser(emptyDetectionLabel)],
                            shape: EMPTY_SHAPE,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape]);
                    });

                    const expectedAnnotation = {
                        shape,
                        labels: [],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('does not remove an empty segmentation annotation when adding a detection annotation', () => {
                    const annotations: Annotation[] = [
                        getMockedAnnotation({
                            id: 'det-1-empty-seg',
                            labels: [labelFromUser(detectionLabel), labelFromUser(emptySegmentationLabel)],
                            shape: { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 10, height: 10 },
                        }),
                        getMockedAnnotation({
                            id: 'det-2',
                            labels: [labelFromUser(detectionLabel)],
                            shape: { shapeType: ShapeType.Rect as const, x: 30, y: 30, width: 20, height: 20 },
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 35, y: 35, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape], [segmentationLabels[1]]);
                    });

                    const expectedAnnotation = {
                        shape,
                        labels: [labelFromUser(segmentationLabels[1])],
                        isSelected: true,
                    };

                    expect(result.current.annotations).toHaveLength(3);
                    expect(result.current.annotations[0]).toEqual(annotations[0]);
                    expect(result.current.annotations[1]).toEqual(annotations[1]);
                    expect(result.current.annotations[2]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                // empty classification label
                it('sets an empty segmentation label to a detection annotation', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, [annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptySegmentationLabel),
                    ]);
                });

                // NOTE: make sure we add the annotaiotns inside of a detection annotation, add another detection annotation
                // to be sure..
                it('removes other segmentation annotations when assigning empty label to a detection annotation', () => {
                    const annotations = [
                        // Detection annotation with 2 segmentation annotations
                        getMockedAnnotation({
                            id: 'det-1',
                            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-1-seg-2',
                            shape: { shapeType: ShapeType.Rect, x: 20, y: 20, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                        // Detection annotation with 1 segmentation annotation
                        getMockedAnnotation({
                            id: 'det-2',
                            shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: true,
                        }),
                        getMockedAnnotation({
                            id: 'det-2-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 170, y: 170, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: true,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, [annotations[0].id]);
                    });

                    expect(result.current.annotations).toHaveLength(3);
                    expect(result.current.annotations[0].labels).toEqual([
                        labelFromUser(detectionLabel),
                        labelFromUser(emptySegmentationLabel),
                    ]);
                    expect(getIds([...result.current.annotations])).toEqual(['det-1', 'det-2', 'det-2-seg-1']);
                });

                it('removes the empty segmentation label when adding a new shape in a detection annotation', () => {
                    const annotations = [
                        // Detection annotation without segmentation annotations
                        getMockedAnnotation({
                            id: 'det-1',
                            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                            labels: [labelFromUser(detectionLabel), labelFromUser(emptySegmentationLabel)],
                            isSelected: true,
                        }),
                        // Detection annotation with 1 segmentation annotation
                        getMockedAnnotation({
                            id: 'det-2',
                            shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: false,
                        }),
                        getMockedAnnotation({
                            id: 'det-2-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 170, y: 170, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: false,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 35, y: 35, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape], [segmentationLabels[1]]);
                    });

                    expect(result.current.annotations).toHaveLength(4);
                    expect(result.current.annotations[0].labels).toEqual([labelFromUser(detectionLabel)]);
                    expect(result.current.annotations[1]).toEqual(annotations[1]);
                    expect(result.current.annotations[2]).toEqual(annotations[2]);

                    const expectedAnnotation = {
                        shape,
                        labels: [labelFromUser(segmentationLabels[1])],
                        isSelected: true,
                    };
                    expect(result.current.annotations[3]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('removes the empty segmentation label when adding a new shape without label in a detection annotation', () => {
                    const annotations = [
                        // Detection annotation without segmentation annotations
                        getMockedAnnotation({
                            id: 'det-1',
                            shape: { shapeType: ShapeType.Rect, x: 0, y: 0, width: 100, height: 100 },
                            labels: [labelFromUser(detectionLabel), labelFromUser(emptySegmentationLabel)],
                            isSelected: true,
                        }),
                        // Detection annotation with 1 segmentation annotation
                        getMockedAnnotation({
                            id: 'det-2',
                            shape: { shapeType: ShapeType.Rect, x: 150, y: 150, width: 50, height: 50 },
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: false,
                        }),
                        getMockedAnnotation({
                            id: 'det-2-seg-1',
                            shape: { shapeType: ShapeType.Rect, x: 170, y: 170, width: 10, height: 10 },
                            labels: [labelFromUser(segmentationLabels[0])],
                            isSelected: false,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    const shape = { shapeType: ShapeType.Rect as const, x: 35, y: 35, width: 10, height: 10 };
                    act(() => {
                        result.current.addShapes([shape]);
                    });

                    expect(result.current.annotations).toHaveLength(4);
                    expect(result.current.annotations[0].labels).toEqual([labelFromUser(detectionLabel)]);
                    expect(result.current.annotations[1]).toEqual(annotations[1]);
                    expect(result.current.annotations[2]).toEqual(annotations[2]);

                    const expectedAnnotation = {
                        shape,
                        labels: [],
                        isSelected: true,
                    };
                    expect(result.current.annotations[3]).toEqual(expect.objectContaining(expectedAnnotation));
                });

                it('does not allow adding an empty classification label without input', () => {
                    const annotations = [
                        getMockedAnnotation({
                            id: '1',
                            labels: [labelFromUser(detectionLabel)],
                            isSelected: false,
                        }),
                    ];
                    const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                    act(() => {
                        result.current.addLabel(emptySegmentationLabel, []);
                    });

                    expect(result.current.annotations).toHaveLength(1);
                    expect(result.current.annotations).toEqual(annotations);
                });
            });

            it('does not allow adding a detection label to a circle', () => {
                const selectedTask = tasks[0];
                const shape = {
                    shapeType: ShapeType.Circle as const,
                    x: 0,
                    y: 0,
                    r: 10,
                };

                const { result } = renderAnnotationSceneHook({ tasks, annotations: [], selectedTask });

                act(() => {
                    result.current.addShapes([shape], [detectionLabel]);
                });

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0].labels).toHaveLength(0);
            });

            it('does not allow adding a detection label to a polygon', () => {
                const selectedTask = tasks[0];
                const shape = {
                    shapeType: ShapeType.Polygon as const,
                    points: [
                        { x: 0, y: 0 },
                        { x: 0, y: 10 },
                        { x: 10, y: 10 },
                    ],
                };

                const { result } = renderAnnotationSceneHook({ tasks, annotations: [], selectedTask });

                act(() => {
                    result.current.addShapes([shape], [detectionLabel]);
                });

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0].labels).toHaveLength(0);
            });

            it('does not allow adding a detection label to an existing circle', () => {
                const selectedTask = tasks[0];
                const annotations = [
                    getMockedAnnotation({
                        shape: { shapeType: ShapeType.Circle, x: 0, y: 0, r: 10 },
                        labels: [],
                        isSelected: true,
                    }),
                ];

                const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                act(() => {
                    result.current.addLabel(detectionLabel, [annotations[0].id]);
                });

                expect(result.current.annotations).toHaveLength(1);
                expect(result.current.annotations[0].labels).toHaveLength(0);
            });

            it('does not allow adding a detection label to an existing polygon', () => {
                const selectedTask = tasks[0];
                const annotations = [
                    getMockedAnnotation({
                        id: '1',
                        shape: {
                            shapeType: ShapeType.Polygon,
                            points: [
                                { x: 0, y: 0 },
                                { x: 0, y: 10 },
                                { x: 10, y: 10 },
                            ],
                        },
                        labels: [],
                        isSelected: true,
                    }),
                    getMockedAnnotation({
                        id: '2',
                        shape: { shapeType: ShapeType.Circle, x: 0, y: 0, r: 10 },
                        labels: [],
                        isSelected: true,
                    }),
                ];

                const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

                act(() => {
                    result.current.addLabel(detectionLabel, [annotations[0].id, annotations[1].id]);
                });

                expect(result.current.annotations).toHaveLength(2);
                expect(result.current.annotations[0].labels).toHaveLength(0);
                expect(result.current.annotations[1].labels).toHaveLength(0);
            });
        });
    });
});

describe('Anomaly localization tasks', () => {
    const normalLabel = getMockedLabel({
        id: 'normal-label-id',
        name: 'Normal',
        behaviour: LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL,
    });

    const anomalousLabel = getMockedLabel({
        id: 'anomalous-label-id',
        name: 'Anomalous',
        behaviour: LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.ANOMALOUS,
    });

    const tasks = [
        getMockedTask({
            id: 'anomaly-segmentation',
            domain: DOMAIN.ANOMALY_SEGMENTATION,
            labels: [normalLabel, anomalousLabel],
        }),
    ];

    it('Adds a global anomalous label', () => {
        const selectedTask = tasks[0];

        const { result } = renderAnnotationSceneHook({ tasks, annotations: [], selectedTask });

        act(() => {
            result.current.addLabel(anomalousLabel, []);
        });

        expect(result.current.annotations).toHaveLength(1);
        expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
        expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);
    });

    it('Does not remove existing anomalous annotations when attempting to add a global anomalous annotation', () => {
        const selectedTask = tasks[0];

        const annotations = [
            getMockedAnnotation({
                id: 'empty-normal-annotation',
                shape: EMPTY_SHAPE,
                labels: [labelFromUser(anomalousLabel)],
            }),
            getMockedAnnotation({ id: 'annotation-1', labels: [labelFromUser(anomalousLabel)] }),
        ];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

        act(() => {
            result.current.addLabel(anomalousLabel, []);
        });

        expect(result.current.annotations).toHaveLength(2);
        expect(result.current.annotations).toEqual(annotations);
    });

    it('Does not remove existing anomalous annotations when adding a global anomalous annotation', () => {
        const selectedTask = tasks[0];

        const annotations = [getMockedAnnotation({ id: 'annotation-1', labels: [labelFromUser(anomalousLabel)] })];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

        act(() => {
            result.current.addLabel(anomalousLabel, []);
        });

        expect(result.current.annotations).toHaveLength(2);
        expect(result.current.annotations[0]).toEqual(annotations[0]);
        expect(result.current.annotations[1].shape).toEqual(EMPTY_SHAPE);
    });

    it('Adds a global anomalous label when adding a local anomalous label', () => {
        const selectedTask = tasks[0];

        const { result } = renderAnnotationSceneHook({ tasks, annotations: [], selectedTask });

        const shape = { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 } as const;

        act(() => {
            result.current.addShapes([shape], [anomalousLabel]);
        });

        expect(result.current.annotations).toHaveLength(2);

        // First a global label should have been added
        expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
        expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

        // Next the shape we wanted to add should have been added
        expect(result.current.annotations[1].shape).toEqual(shape);
        expect(result.current.annotations[1].labels).toEqual([labelFromUser(anomalousLabel)]);
    });

    it('Does not add a second global anomalous label when adding a local anomalous label', () => {
        const selectedTask = tasks[0];
        const annotations = [
            getMockedAnnotation({
                id: 'global-anomalous-annotation',
                shape: EMPTY_SHAPE,
                labels: [labelFromUser(anomalousLabel)],
            }),
        ];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

        const shape = { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 } as const;

        act(() => {
            result.current.addShapes([shape], [anomalousLabel]);
        });

        expect(result.current.annotations).toHaveLength(2);

        // The global anomalous label should have remained
        expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
        expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

        // Next the shape we wanted to add should have been added
        expect(result.current.annotations[1].shape).toEqual(shape);
        expect(result.current.annotations[1].labels).toEqual([labelFromUser(anomalousLabel)]);
    });

    it('Replaces a global normal label when adding a local anomalous label', () => {
        const selectedTask = tasks[0];
        const annotations = [
            getMockedAnnotation({
                id: 'empty-normal-annotation',
                shape: EMPTY_SHAPE,
                labels: [labelFromUser(normalLabel)],
            }),
        ];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

        const shape = { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 } as const;

        act(() => {
            result.current.addShapes([shape], [anomalousLabel]);
        });

        expect(result.current.annotations).toHaveLength(2);

        // The normal label should have been replaced by a global anomalous label
        expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
        expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

        // Next the shape we wanted to add should have been added
        expect(result.current.annotations[1].shape).toEqual(shape);
        expect(result.current.annotations[1].labels).toEqual([labelFromUser(anomalousLabel)]);
    });

    it('Replaces a global annotation without labels when adding a local anomalous label', () => {
        const selectedTask = tasks[0];
        const annotations = [
            getMockedAnnotation({
                id: 'empty-global-annotation',
                shape: EMPTY_SHAPE,
                labels: [],
            }),
        ];

        const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

        const shape = { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 } as const;

        act(() => {
            result.current.addShapes([shape], [anomalousLabel]);
        });

        expect(result.current.annotations).toHaveLength(2);

        // The normal label should have been replaced by a global anomalous label
        expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
        expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

        // Next the shape we wanted to add should have been added
        expect(result.current.annotations[1].shape).toEqual(shape);
        expect(result.current.annotations[1].labels).toEqual([labelFromUser(anomalousLabel)]);
    });

    describe('addAnnotations', () => {
        it('Adds a global anomalous label when adding a local anomalous label', () => {
            const selectedTask = tasks[0];

            const { result } = renderAnnotationSceneHook({ tasks, annotations: [], selectedTask });

            const shape = { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 } as const;

            act(() => {
                result.current.addAnnotations([
                    getMockedAnnotation({ id: 'new-annotation', labels: [labelFromUser(anomalousLabel)], shape }),
                ]);
            });

            expect(result.current.annotations).toHaveLength(2);

            // First a global label should have been added
            expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
            expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

            // Next the shape we wanted to add should have been added
            expect(result.current.annotations[1].shape).toEqual(shape);
            expect(result.current.annotations[1].labels).toEqual([labelFromUser(anomalousLabel)]);
        });

        it('Does not add a second global anomalous label when adding a local anomalous label', () => {
            const selectedTask = tasks[0];
            const annotations = [
                getMockedAnnotation({
                    id: 'global-anomalous-annotation',
                    shape: EMPTY_SHAPE,
                    labels: [labelFromUser(anomalousLabel)],
                }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

            const shape = { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 } as const;

            act(() => {
                result.current.addAnnotations([
                    getMockedAnnotation({ id: 'new-annotation', labels: [labelFromUser(anomalousLabel)], shape }),
                ]);
            });

            expect(result.current.annotations).toHaveLength(2);

            // The global anomalous label should have remained
            expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
            expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

            // Next the shape we wanted to add should have been added
            expect(result.current.annotations[1].shape).toEqual(shape);
            expect(result.current.annotations[1].labels).toEqual([labelFromUser(anomalousLabel)]);
        });

        it('Replaces a global normal label when adding a local anomalous label', () => {
            const selectedTask = tasks[0];
            const annotations = [
                getMockedAnnotation({
                    id: 'empty-normal-annotation',
                    shape: EMPTY_SHAPE,
                    labels: [labelFromUser(normalLabel)],
                }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

            const shape = { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 } as const;

            act(() => {
                result.current.addAnnotations([
                    getMockedAnnotation({ id: 'new-annotation', labels: [labelFromUser(anomalousLabel)], shape }),
                ]);
            });

            expect(result.current.annotations).toHaveLength(2);

            // The normal label should have been replaced by a global anomalous label
            expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
            expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

            // Next the shape we wanted to add should have been added
            expect(result.current.annotations[1].shape).toEqual(shape);
            expect(result.current.annotations[1].labels).toEqual([labelFromUser(anomalousLabel)]);
        });

        it('does not remove local anomalous annotations', () => {
            const selectedTask = tasks[0];
            const annotations = [
                getMockedAnnotation({
                    id: 'global-anomalous-annotation',
                    shape: EMPTY_SHAPE,
                    labels: [labelFromUser(anomalousLabel)],
                }),
                getMockedAnnotation({
                    id: 'local-anomalous-annotation-1',
                    shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 30, height: 30 },
                    labels: [labelFromUser(anomalousLabel)],
                }),
                getMockedAnnotation({
                    id: 'local-anomalous-annotation-2',
                    shape: { shapeType: ShapeType.Rect, x: 30, y: 30, width: 30, height: 30 },
                    labels: [labelFromUser(anomalousLabel)],
                }),
            ];

            const { result } = renderAnnotationSceneHook({ tasks, annotations, selectedTask });

            const shape = { shapeType: ShapeType.Rect, x: 20, y: 20, width: 30, height: 30 } as const;

            act(() => {
                result.current.addAnnotations([
                    getMockedAnnotation({ id: 'new-annotation', labels: [labelFromUser(anomalousLabel)], shape }),
                ]);
            });

            expect(result.current.annotations).toHaveLength(4);

            // The global anomalous label should have remained
            expect(result.current.annotations[0].shape).toEqual(EMPTY_SHAPE);
            expect(result.current.annotations[0].labels).toEqual([labelFromUser(anomalousLabel)]);

            // Next the shape we wanted to add should have been added
            expect(result.current.annotations[3].shape).toEqual(shape);
            expect(result.current.annotations[3].labels).toEqual([labelFromUser(anomalousLabel)]);
        });
    });
});
