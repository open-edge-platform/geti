// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedLabel } from '../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask } from '../../test-utils/mocked-items-factory/mocked-tasks';
import { isPrediction } from '../labels/utils';
import { AnnotationStatePerTask, MEDIA_ANNOTATION_STATUS } from '../media/base.interface';
import { getAnnotationStateForTask, labelFromUser } from './utils';

describe('getAnnotationStateForTask', () => {
    describe('partially annotated chainTask', () => {
        test('when all tasks are annotated it returns annotated', () => {
            expect(
                getAnnotationStateForTask([
                    { taskId: 'task_a', state: MEDIA_ANNOTATION_STATUS.ANNOTATED },
                    { taskId: 'task_b', state: MEDIA_ANNOTATION_STATUS.ANNOTATED },
                ])
            ).toBe(MEDIA_ANNOTATION_STATUS.ANNOTATED);
        });

        test('when one of the tasks is not annotated it returns partially_annotated', () => {
            expect(
                getAnnotationStateForTask([
                    { taskId: 'task_a', state: MEDIA_ANNOTATION_STATUS.ANNOTATED },
                    { taskId: 'task_b', state: MEDIA_ANNOTATION_STATUS.NONE },
                ])
            ).toBe(MEDIA_ANNOTATION_STATUS.PARTIALLY_ANNOTATED);
        });

        test('when none of the tasks is annotated it returns none', () => {
            expect(
                getAnnotationStateForTask([
                    { taskId: 'task_a', state: MEDIA_ANNOTATION_STATUS.NONE },
                    { taskId: 'task_b', state: MEDIA_ANNOTATION_STATUS.NONE },
                ])
            ).toBe(MEDIA_ANNOTATION_STATUS.NONE);
        });
    });

    describe('completely annotated chainTask', () => {
        const chainTaskData: AnnotationStatePerTask[] = [
            { taskId: 'task_a', state: MEDIA_ANNOTATION_STATUS.ANNOTATED },
            { taskId: 'task_b', state: MEDIA_ANNOTATION_STATUS.ANNOTATED },
        ];

        test('when annotated task is selected returns annotated', () => {
            expect(getAnnotationStateForTask(chainTaskData)).toBe(MEDIA_ANNOTATION_STATUS.ANNOTATED);
        });

        test('when no task is selected returns annotated', () => {
            expect(getAnnotationStateForTask(chainTaskData)).toBe(MEDIA_ANNOTATION_STATUS.ANNOTATED);
        });
    });

    describe('completely not-annotated chainTask', () => {
        const chainTaskData: AnnotationStatePerTask[] = [
            { taskId: 'task_a', state: MEDIA_ANNOTATION_STATUS.NONE },
            { taskId: 'task_b', state: MEDIA_ANNOTATION_STATUS.NONE },
        ];

        test('when a task is selected returns none', () => {
            expect(getAnnotationStateForTask(chainTaskData)).toBe(MEDIA_ANNOTATION_STATUS.NONE);
            expect(getAnnotationStateForTask(chainTaskData)).toBe(MEDIA_ANNOTATION_STATUS.NONE);
        });

        test('when no task is selected returns none', () => {
            expect(getAnnotationStateForTask(chainTaskData)).toBe(MEDIA_ANNOTATION_STATUS.NONE);
        });
    });

    describe('state per task', () => {
        const chainTaskData: AnnotationStatePerTask[] = [
            { taskId: 'task_a', state: MEDIA_ANNOTATION_STATUS.ANNOTATED },
            { taskId: 'task_b', state: MEDIA_ANNOTATION_STATUS.TO_REVISIT },
        ];

        const task = getMockedTask({ id: 'task_a' });
        const otherTask = getMockedTask({ id: 'task_c' });

        test('it returns the state of the given task', () => {
            expect(getAnnotationStateForTask(chainTaskData, task)).toBe(MEDIA_ANNOTATION_STATUS.ANNOTATED);
        });

        test("it defaults to none if the task's state is not found", () => {
            expect(getAnnotationStateForTask(chainTaskData, otherTask)).toBe(MEDIA_ANNOTATION_STATUS.NONE);
        });
    });
});

it('isPrediction', () => {
    expect(isPrediction(labelFromUser(getMockedLabel({})))).toBe(false);

    expect(
        isPrediction({
            ...getMockedLabel({}),
            source: { modelId: undefined, modelStorageId: undefined },
            score: 0.1,
        })
    ).toBe(true);

    expect(
        isPrediction({
            ...getMockedLabel({}),
            source: { modelId: '123', modelStorageId: '321', userId: 'test@email.com' },
            score: 0.1,
        })
    ).toBe(false);

    expect(
        isPrediction({
            ...getMockedLabel({}),
            source: { modelId: '123', modelStorageId: '321' },
            score: 0.1,
        })
    ).toBe(true);
});
