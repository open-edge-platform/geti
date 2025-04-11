// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels as mockedLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import {
    getGlobalAnnotations,
    getInputForTask,
    getLabelConflictPredicate,
    getOutputFromTask,
    getPreviousTask,
} from './utils';

describe('getPreviousTask', () => {
    describe('returns undefined if there is no previous task', () => {
        it('for single task projects', () => {
            const tasks = [getMockedTask({ id: '1' })];
            const selectedTask = tasks[0];

            expect(getPreviousTask(tasks, selectedTask)).toBe(null);
        });

        it('when the first task in a chain is selected', () => {
            const tasks = [getMockedTask({ id: '1' }), getMockedTask({ id: '2' })];
            const selectedTask = tasks[0];

            expect(getPreviousTask(tasks, selectedTask)).toEqual(null);
        });

        it('when the "All tasks" task is slected', () => {
            const tasks = [getMockedTask({ id: '1' }), getMockedTask({ id: '2' })];
            const selectedTask = null;

            expect(getPreviousTask(tasks, selectedTask)).toEqual(null);
        });
    });

    it('returns the previous task', () => {
        const tasks = [getMockedTask({ id: '1' }), getMockedTask({ id: '2' })];
        const selectedTask = tasks[1];

        expect(getPreviousTask(tasks, selectedTask)).toEqual(tasks[0]);
    });
});

describe('getOutputFromTask', () => {
    describe('single tasks projects', () => {
        it('returns annotations from the single task', () => {
            const tasks = [getMockedTask({ id: '1' })];
            const selectedTask = tasks[0];
            const annotations = [
                getMockedAnnotation({ id: '1' }),
                getMockedAnnotation({ id: '2' }),
                getMockedAnnotation({ id: '3' }),
                getMockedAnnotation({ id: '4' }),
            ];

            expect(getOutputFromTask(annotations, tasks, selectedTask)).toEqual(annotations);
        });
    });

    const [firstLabel, ...otherLabels] = mockedLabels;
    //
    // local -> global task chains
    describe.each([
        [
            'detection -> classification',
            getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: [firstLabel] }),
            getMockedTask({ id: '2', domain: DOMAIN.CLASSIFICATION, labels: otherLabels }),
        ],
        [
            'segmentation -> classification',
            getMockedTask({ id: '1', domain: DOMAIN.SEGMENTATION, labels: [firstLabel] }),
            getMockedTask({ id: '2', domain: DOMAIN.CLASSIFICATION, labels: otherLabels }),
        ],
    ])('local -> global task chains (%s)', (_, localTask, globalTask) => {
        const annotations = [
            getMockedAnnotation({ id: '1', labels: [] }),
            getMockedAnnotation({ id: '2', labels: [labelFromUser(firstLabel)] }),
            getMockedAnnotation({ id: '3', labels: [labelFromUser(firstLabel)], isSelected: true }),
            getMockedAnnotation({
                id: '4',
                labels: [labelFromUser(firstLabel), labelFromUser(otherLabels[0])],
            }),
            getMockedAnnotation({
                id: '5',
                labels: [labelFromUser(firstLabel), labelFromUser(otherLabels[0])],
            }),
        ];
        const tasks = [localTask, globalTask];

        it('returns all annotations if "All tasks" is selected', () => {
            expect(getOutputFromTask(annotations, tasks, null)).toEqual(annotations);
        });

        it('returns the annotations from the first task', () => {
            expect(getOutputFromTask(annotations, tasks, localTask)).toEqual(annotations);
            expect(getInputForTask(annotations, tasks, localTask)).toEqual([]);
        });

        it('returns the annotations from the second task if they are inside selected annotations of the first task', () => {
            expect(getOutputFromTask(annotations, tasks, globalTask)).toEqual(annotations);
            expect(getInputForTask(annotations, tasks, globalTask)).toEqual(annotations);
        });
    });

    describe.each([
        [
            'detection -> segmentation',
            getMockedTask({ id: '1', domain: DOMAIN.DETECTION, labels: [firstLabel] }),
            getMockedTask({ id: '2', domain: DOMAIN.SEGMENTATION, labels: otherLabels }),
        ],
        [
            'segmentation -> detection',
            getMockedTask({ id: '1', domain: DOMAIN.SEGMENTATION, labels: [firstLabel] }),
            getMockedTask({ id: '2', domain: DOMAIN.DETECTION, labels: otherLabels }),
        ],
    ])('global -> global task chains (%s)', (_, firstTask, secondTask) => {
        const tasks = [firstTask, secondTask];
        const annotations = [
            getMockedAnnotation({ id: '1', labels: [] }),
            getMockedAnnotation({
                id: '2',
                labels: [labelFromUser(firstLabel)],
                shape: {
                    shapeType: ShapeType.Rect,
                    x: 100,
                    y: 100,
                    width: 100,
                    height: 100,
                },
            }),
            getMockedAnnotation({ id: '3', labels: [labelFromUser(firstLabel)], isSelected: true }),
            getMockedAnnotation({
                id: '4',
                labels: [labelFromUser(otherLabels[0])],
            }),
            getMockedAnnotation({
                id: '5',
                labels: [labelFromUser(otherLabels[0])],
                shape: {
                    shapeType: ShapeType.Rect,
                    x: 110,
                    y: 110,
                    width: 10,
                    height: 10,
                },
            }),
            getMockedAnnotation({
                id: '6',
                labels: [],
                shape: {
                    shapeType: ShapeType.Circle,
                    x: 20,
                    y: 20,
                    r: 10,
                },
            }),
        ];

        it('returns all annotations if "All tasks" is selected', () => {
            expect(getOutputFromTask(annotations, tasks, null)).toEqual(annotations);
            expect(getInputForTask(annotations, tasks, null)).toEqual([]);
        });

        it('returns the annotations from the first task', () => {
            // Only annotations that have a detection label, or no labels at all are returned
            const expectedAnnotations =
                firstTask.domain === DOMAIN.DETECTION
                    ? [annotations[0], annotations[1], annotations[2]]
                    : [annotations[0], annotations[1], annotations[2], annotations[5]];

            expect(getOutputFromTask(annotations, tasks, tasks[0])).toEqual(expectedAnnotations);
            expect(getInputForTask(annotations, tasks, tasks[0])).toEqual([]);
        });

        it('returns the annotations from the second task if they are inside selected annotations of the first task', () => {
            // Only annotations that have a detection label, or no labels at all are returned
            const expectedAnnotations =
                firstTask.domain === DOMAIN.DETECTION
                    ? [annotations[0], annotations[3], annotations[5]]
                    : [annotations[0], annotations[3]];

            expect(getOutputFromTask(annotations, tasks, tasks[1])).toEqual(expectedAnnotations);
            expect(getInputForTask(annotations, tasks, tasks[1])).toEqual([annotations[1], annotations[2]]);
        });

        it('does not consider an unlabeled annotation from a parent task as its output', () => {
            const internalTasks = [firstTask, secondTask];
            const internalAnnotations = [getMockedAnnotation({ id: '1', labels: [], isSelected: true })];

            expect(getOutputFromTask(internalAnnotations, internalTasks, firstTask)).toEqual(internalAnnotations);
            expect(getOutputFromTask(internalAnnotations, internalTasks, secondTask)).toEqual([]);

            expect(getInputForTask(internalAnnotations, internalTasks, internalTasks[1])).toEqual([]);
        });
    });
});

describe('getLabelConflictPredicate', () => {
    it('local labels', () => {
        const localOne = getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, group: '1' });
        const localTwo = getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, group: '2' });
        expect(getLabelConflictPredicate([])(localOne, localTwo)).toBe(true);
    });

    it('same group', () => {
        const localOne = getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, group: '1' });
        const localTwo = getMockedLabel({ behaviour: LABEL_BEHAVIOUR.GLOBAL, group: '1' });
        expect(getLabelConflictPredicate([])(localOne, localTwo)).toBe(true);
    });
});

describe('getGlobalAnnotations', () => {
    const roi = { x: 0, y: 0, width: 100, height: 100 };

    it('returns an empty list when there are only local annotations', () => {
        const annotations: Annotation[] = [
            getMockedAnnotation({
                shape: { shapeType: ShapeType.Rect, ...roi },
                labels: [labelFromUser(getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL }))],
            }),
            getMockedAnnotation({
                shape: { shapeType: ShapeType.Circle, x: 10, y: 10, r: 5 },
                labels: [labelFromUser(getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL }))],
            }),
        ];
        expect(getGlobalAnnotations(annotations, roi, null)).toEqual([]);
    });

    it('returns the selected input annotation', () => {
        const inputAnnotation = getMockedAnnotation({
            shape: { shapeType: ShapeType.Rect, ...roi },
            labels: [labelFromUser(getMockedLabel({ behaviour: LABEL_BEHAVIOUR.GLOBAL }))],
            isSelected: true,
        });

        const annotations: Annotation[] = [inputAnnotation];
        const task = getMockedTask({ domain: DOMAIN.CLASSIFICATION });
        expect(getGlobalAnnotations(annotations, roi, task)).toEqual([inputAnnotation]);
    });

    it('returns an annotation with a global label and shape equal to the ROI', () => {
        const inputAnnotation = getMockedAnnotation({
            shape: { shapeType: ShapeType.Rect, ...roi },
            labels: [labelFromUser(getMockedLabel({ behaviour: LABEL_BEHAVIOUR.GLOBAL }))],
            isSelected: true,
        });

        const annotations: Annotation[] = [inputAnnotation];
        expect(getGlobalAnnotations(annotations, roi, null)).toEqual([inputAnnotation]);
    });

    it('ignores annotations that have both local and global labels', () => {
        const inputAnnotation = getMockedAnnotation({
            shape: { shapeType: ShapeType.Rect, ...roi },
            labels: [
                labelFromUser(getMockedLabel({ behaviour: LABEL_BEHAVIOUR.GLOBAL })),
                labelFromUser(getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL })),
            ],
            isSelected: true,
        });

        const annotations: Annotation[] = [inputAnnotation];
        expect(getGlobalAnnotations(annotations, roi, null)).toEqual([]);
    });
});
