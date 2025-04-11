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

import { renderHook } from '@testing-library/react';

import { Label, LABEL_BEHAVIOUR } from '../../../core/labels/label.interface';
import { getFlattenedLabels, GROUP_SEPARATOR } from '../../../core/labels/utils';
import { DOMAIN } from '../../../core/projects/core.interface';
import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask } from '../../../test-utils/mocked-items-factory/mocked-tasks';
import { useFilteredTaskMetadata } from './use-filtered-task-metadata.hook';

const getMockedLabels = (length: number, label?: Partial<Label>) =>
    Array.from({ length }, (_, index) =>
        getMockedLabel({ ...label, name: `${label?.name}-${index}`, id: `${label?.name}-${index}` })
    );

const noObjectLabel = getMockedLabel({
    name: 'No object',
    group: 'no Object',
    behaviour: LABEL_BEHAVIOUR.ANOMALOUS,
    isEmpty: true,
});

describe('useFilteredTaskMetadata', () => {
    describe('single project', () => {
        it('empty input and includes "noObject/emptyLabels"', () => {
            const domain = DOMAIN.CLASSIFICATION;
            const labels = [...getMockedLabels(4, { name: 'label', group: 'default', isEmpty: false }), noObjectLabel];

            const tasks = [getMockedTask({ labels, domain })];

            const { result } = renderHook(() =>
                useFilteredTaskMetadata({
                    input: '',
                    tasks,
                    selectedTask: null,
                })
            );

            expect(result.current).toHaveLength(1);
            const [metadata] = result.current;

            expect(metadata.domain).toEqual(domain);

            expect(getFlattenedLabels(metadata.labels)).toEqual(
                expect.arrayContaining([...labels, noObjectLabel].map((label) => expect.objectContaining(label)))
            );
        });

        it('empty input and excludes "noObject/emptyLabels"', () => {
            const domain = DOMAIN.CLASSIFICATION;
            const labels = [...getMockedLabels(4, { name: 'label', group: 'default', isEmpty: false }), noObjectLabel];

            const tasks = [getMockedTask({ labels, domain })];

            const { result } = renderHook(() =>
                useFilteredTaskMetadata({
                    input: '',
                    tasks,
                    selectedTask: null,
                    includesEmptyLabels: false,
                })
            );

            expect(result.current).toHaveLength(1);
            const [metadata] = result.current;

            expect(metadata.domain).toEqual(domain);

            expect(getFlattenedLabels(metadata.labels)).not.toEqual(
                expect.arrayContaining([noObjectLabel].map((label) => expect.objectContaining(label)))
            );
        });

        it('no matched labels', () => {
            const domain = DOMAIN.CLASSIFICATION;
            const labels = [...getMockedLabels(4, { name: 'label', group: 'default', isEmpty: false }), noObjectLabel];

            const tasks = [getMockedTask({ labels, domain })];

            const { result } = renderHook(() =>
                useFilteredTaskMetadata({
                    input: 'input test',
                    tasks,
                    selectedTask: null,
                })
            );

            expect(result.current).toHaveLength(0);
        });

        it('partial matches multiple labels', () => {
            const domain = DOMAIN.CLASSIFICATION;
            const input = '1';

            const labels = [
                getMockedLabel({ id: 'a1', name: 'a1', group: 'default' }),
                getMockedLabel({ id: 'a2', name: 'a2', group: 'default' }),
                getMockedLabel({ id: 'b1', name: 'b1', group: 'default' }),
                getMockedLabel({ id: 'b2', name: 'b2', group: 'default' }),
                noObjectLabel,
            ];

            const tasks = [getMockedTask({ labels, domain })];

            const { result } = renderHook(() => useFilteredTaskMetadata({ input, tasks, selectedTask: null }));

            const [metadata] = result.current;

            expect(metadata.domain).toEqual(domain);

            const flattenedLabels = getFlattenedLabels(metadata.labels);
            expect(flattenedLabels).toHaveLength(2);

            flattenedLabels.forEach(({ name }) => expect(name).toContain(input));
        });
    });

    describe('task chain', () => {
        const detectionGroup = 'Detection labels';
        const detectionLabel = getMockedLabel({
            id: 'detection-label-1',
            name: 'detection-label-1',
            group: detectionGroup,
        });

        const classificationLabels = [
            getMockedLabel({
                id: 'classification-label-1',
                name: 'classification-label-1',
                group: `${detectionGroup}${GROUP_SEPARATOR}group1`,
                parentLabelId: detectionLabel.id,
            }),
            getMockedLabel({
                id: 'classification-label-2',
                name: 'classification-label-2',
                group: `${detectionGroup}${GROUP_SEPARATOR}group1`,
                parentLabelId: detectionLabel.id,
            }),
            getMockedLabel({
                id: 'classification-label-3',
                name: 'classification-label-3',
                group: `${detectionGroup}${GROUP_SEPARATOR}group2`,
                parentLabelId: detectionLabel.id,
            }),
            getMockedLabel({
                id: 'classification-label-4',
                name: 'classification-label-4',
                group: `${detectionGroup}${GROUP_SEPARATOR}group2`,
                parentLabelId: detectionLabel.id,
            }),
        ];

        const tasks = [
            getMockedTask({ id: 'task-1', labels: [detectionLabel, noObjectLabel], domain: DOMAIN.DETECTION }),
            getMockedTask({ id: 'task-2', labels: classificationLabels, domain: DOMAIN.CLASSIFICATION }),
        ];

        describe('All tasks', () => {
            it('empty input', () => {
                const { result } = renderHook(() => useFilteredTaskMetadata({ input: '', tasks, selectedTask: null }));

                expect(result.current).toEqual(
                    expect.arrayContaining([
                        expect.objectContaining({ domain: DOMAIN.DETECTION }),
                        expect.objectContaining({ domain: DOMAIN.CLASSIFICATION }),
                    ])
                );

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));

                const tasksLabels = tasks.flatMap(({ labels }) => labels);

                expect(flattenLabels).toHaveLength(tasksLabels.length);

                expect(flattenLabels).toEqual(
                    expect.arrayContaining(tasksLabels.map((label) => expect.objectContaining(label)))
                );
            });

            it('matches one label on second task', () => {
                const input = 'label-2';
                const { result } = renderHook(() => useFilteredTaskMetadata({ input, tasks, selectedTask: null }));

                expect(result.current).toEqual(
                    expect.arrayContaining([expect.objectContaining({ domain: DOMAIN.CLASSIFICATION })])
                );

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));

                expect(flattenLabels).toHaveLength(1);
                flattenLabels.forEach(({ name }) => expect(name).toContain(input));
            });

            it('matches labels from both tasks', () => {
                const input = 'label-1';
                const { result } = renderHook(() => useFilteredTaskMetadata({ input, tasks, selectedTask: null }));

                expect(result.current).toEqual(
                    expect.arrayContaining([
                        expect.objectContaining({ domain: DOMAIN.DETECTION }),
                        expect.objectContaining({ domain: DOMAIN.CLASSIFICATION }),
                    ])
                );

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));

                expect(flattenLabels).toHaveLength(2);
                flattenLabels.forEach(({ name }) => expect(name).toContain(input));
            });

            it('no matches and excludes "noObject/emptyLabels"', () => {
                const { result } = renderHook(() =>
                    useFilteredTaskMetadata({
                        tasks,
                        input: noObjectLabel.name,
                        selectedTask: null,
                        includesEmptyLabels: false,
                    })
                );

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));
                expect(flattenLabels).toEqual([]);
            });
        });

        describe('first task', () => {
            const selectedTask = tasks[0];

            it('partial matches one label', () => {
                const input = 'label-1';
                const [matchLabel] = selectedTask.labels;
                const { result } = renderHook(() => useFilteredTaskMetadata({ input, tasks, selectedTask }));

                expect(result.current).toEqual(
                    expect.arrayContaining([expect.objectContaining({ domain: selectedTask.domain })])
                );

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));
                expect(flattenLabels).toHaveLength(1);

                flattenLabels.forEach(({ name }) => expect(name).toContain(matchLabel.name));
            });

            it('no matches', () => {
                const input = 'test';

                const { result } = renderHook(() => useFilteredTaskMetadata({ input, tasks, selectedTask }));

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));
                expect(flattenLabels).toEqual([]);
            });
        });

        describe('second task', () => {
            const selectedTask = tasks[1];

            it('empty input', () => {
                const { result } = renderHook(() => useFilteredTaskMetadata({ input: '', tasks, selectedTask }));

                expect(result.current).toEqual(
                    expect.arrayContaining([expect.objectContaining({ domain: selectedTask.domain })])
                );

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));

                expect(flattenLabels).toHaveLength(selectedTask.labels.length);

                expect(flattenLabels).toEqual(
                    expect.arrayContaining(selectedTask.labels.map((label) => expect.objectContaining(label)))
                );
            });

            it('partial matches one label', () => {
                const input = 'label-1';
                const { result } = renderHook(() => useFilteredTaskMetadata({ input, tasks, selectedTask }));

                expect(result.current).toEqual(
                    expect.arrayContaining([expect.objectContaining({ domain: selectedTask.domain })])
                );

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));
                expect(flattenLabels).toHaveLength(1);

                flattenLabels.forEach(({ name }) => expect(name).toContain(input));
            });

            it('no matches', () => {
                const input = 'test';

                const { result } = renderHook(() => useFilteredTaskMetadata({ input, tasks, selectedTask }));

                const flattenLabels = result.current.flatMap((metadata) => getFlattenedLabels(metadata.labels));
                expect(flattenLabels).toEqual([]);
            });
        });
    });
});
