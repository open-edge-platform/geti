// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedTreeGroup, getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProjectDTO } from '../../../test-utils/mocked-items-factory/mocked-project';
import { LABEL_BEHAVIOUR, LabelsRelationType } from '../../labels/label.interface';
import { DOMAIN } from '../core.interface';
import { ProjectDTO } from '../dtos/project.interface';
import { TASK_TYPE } from '../dtos/task.interface';
import { TaskMetadata } from './../task.interface';
import { getPreparedTasks, getProjectEntity, getRawNewLabel } from './utils';

describe('Project service utils', () => {
    describe('getRawNewLabel', () => {
        it('Behaviour is 0', () => {
            const newLabel = getRawNewLabel({
                color: 'color-test',
                group: 'group-test',
                id: 'id-test',
                name: 'name-test',
                parent_id: 'parentId-test',
                is_empty: false,
                is_anomalous: false,
                is_background: false,
            });
            expect(newLabel.behaviour).toBe(LABEL_BEHAVIOUR.LOCAL);
        });
    });

    describe('getProjectEntity', () => {
        it('Check if labels are sorted by hierarchy order', () => {
            const projectDTO: ProjectDTO = getMockedProjectDTO({}, [
                {
                    id: 'label-2',
                    color: '#edffee',
                    name: 'Label 2',
                    group: 'group 1',
                    is_anomalous: false,
                    is_empty: false,
                    is_background: false,
                    parent_id: 'label-1',
                },
                {
                    id: 'label-1',
                    color: '#edffee',
                    name: 'Label 1',
                    group: 'group 1',
                    is_anomalous: false,
                    is_empty: false,
                    is_background: false,
                    parent_id: null,
                },
                {
                    id: 'label-4',
                    color: '#edffee',
                    name: 'Label 4',
                    group: 'group 1',
                    is_anomalous: false,
                    is_empty: false,
                    is_background: false,
                    parent_id: 'label-3',
                },
                {
                    id: 'label-3',
                    color: '#edffee',
                    name: 'Label 3',
                    group: 'group 1',
                    is_anomalous: false,
                    is_empty: false,
                    is_background: false,
                    parent_id: 'label-1',
                },
            ]);
            const projectEntity = getProjectEntity(projectDTO);

            expect(projectEntity.labels).toStrictEqual([
                expect.objectContaining({
                    id: 'label-1',
                    group: 'group 1',
                    name: 'Label 1',
                    hotkey: undefined,
                    color: '#edffee',
                    parentLabelId: null,
                    behaviour: LABEL_BEHAVIOUR.GLOBAL,
                }),
                expect.objectContaining({
                    id: 'label-2',
                    group: 'group 1',
                    name: 'Label 2',
                    hotkey: undefined,
                    color: '#edffee',
                    parentLabelId: 'label-1',
                    behaviour: LABEL_BEHAVIOUR.GLOBAL,
                }),
                expect.objectContaining({
                    id: 'label-3',
                    group: 'group 1',
                    name: 'Label 3',
                    hotkey: undefined,
                    color: '#edffee',
                    parentLabelId: 'label-1',
                    behaviour: LABEL_BEHAVIOUR.GLOBAL,
                }),
                expect.objectContaining({
                    id: 'label-4',
                    group: 'group 1',
                    name: 'Label 4',
                    hotkey: undefined,
                    color: '#edffee',
                    parentLabelId: 'label-3',
                    behaviour: LABEL_BEHAVIOUR.GLOBAL,
                }),
            ]);
        });

        it('returns keypoint structure', () => {
            const label = {
                id: 'label-2',
                color: '#edffee',
                name: 'Label 2',
                group: 'group 1',
                is_anomalous: false,
                is_empty: false,
                is_background: false,
                parent_id: 'label-1',
            };

            const projectDTO = getMockedProjectDTO({}, [label]);
            projectDTO.pipeline.tasks = [
                {
                    id: 'task-id',
                    title: 'Task',
                    labels: [label],
                    task_type: TASK_TYPE.KEYPOINT_DETECTION,
                    keypoint_structure: { positions: [{ x: 0, y: 0, label: label.id }], edges: [] },
                },
            ];

            expect(getProjectEntity(projectDTO).tasks[0]).toEqual(
                expect.objectContaining({
                    keypointStructure: {
                        edges: [],
                        positions: [
                            {
                                x: 0,
                                y: 0,
                                edgeEnds: [],
                                isVisible: true,
                                isSelected: false,
                                label: expect.objectContaining({ id: label.id, name: label.name }),
                            },
                        ],
                    },
                })
            );
        });
    });

    describe('getTasks', () => {
        it('returns correct payload with label and group names trimmed', () => {
            const mockTaskMetadata: TaskMetadata = {
                labels: [
                    getMockedTreeGroup({
                        name: 'Animal',
                        children: [
                            // Label with spaces after
                            getMockedTreeLabel({ name: 'Cat         ' }),
                            getMockedTreeLabel({
                                name: 'Dog',
                                children: [
                                    getMockedTreeGroup({
                                        // Group with spaces after
                                        name: 'Color     ',
                                        children: [
                                            // Label with spaces before
                                            getMockedTreeLabel({ name: '     White' }),
                                            getMockedTreeLabel({ name: 'Black' }),
                                            getMockedTreeLabel({ name: 'Mixed' }),
                                        ],
                                    }),
                                ],
                            }),
                            getMockedTreeLabel({ name: 'Hamster' }),
                        ],
                    }),
                ],
                domain: DOMAIN.CLASSIFICATION,
                relation: LabelsRelationType.SINGLE_SELECTION,
            };

            expect(getPreparedTasks([mockTaskMetadata], [DOMAIN.CLASSIFICATION])).toEqual([
                { task_type: 'dataset', title: 'Dataset' },
                {
                    labels: [
                        expect.objectContaining({
                            color: 'blue',
                            group: 'group-1',
                            hotkey: undefined,
                            name: 'Cat',
                            parent_id: null,
                        }),
                        expect.objectContaining({
                            color: 'blue',
                            group: 'group-1',
                            hotkey: undefined,
                            name: 'Dog',
                            parent_id: null,
                        }),
                        expect.objectContaining({
                            color: 'blue',
                            group: 'group-1',
                            hotkey: undefined,
                            name: 'White',
                            parent_id: null,
                        }),
                        expect.objectContaining({
                            color: 'blue',
                            group: 'group-1',
                            hotkey: undefined,
                            name: 'Black',
                            parent_id: null,
                        }),
                        expect.objectContaining({
                            color: 'blue',
                            group: 'group-1',
                            hotkey: undefined,
                            name: 'Mixed',
                            parent_id: null,
                        }),
                        expect.objectContaining({
                            color: 'blue',
                            group: 'group-1',
                            hotkey: undefined,
                            name: 'Hamster',
                            parent_id: null,
                        }),
                    ],
                    task_type: 'classification',
                    title: 'Classification',
                },
            ]);
        });
    });
});
