// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { LabelItemType } from '../label-tree-view.interface';
import { Label, LABEL_BEHAVIOUR, LabelsRelationType } from '../label.interface';
import { getFlattenedGroups, getFlattenedLabels, GROUP_SEPARATOR } from '../utils';
import { fetchLabelsTree, fetchLabelsTreeWithGroups } from './labels-utils';

describe('Function fetchLabelsTreeWithGroups', () => {
    it('One label return hierarchy with one group and one label in children', () => {
        const labels = [getMockedLabel({ name: 'detection', group: 'Default group root task' })];
        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);

        expect(result).toHaveLength(1);
        expect(result[0].children).toHaveLength(1);
        expect(result[0]).toStrictEqual(
            expect.objectContaining({
                name: 'Default group root task',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
            })
        );
        expect(result[0].children[0]).toStrictEqual(
            expect.objectContaining({ name: 'detection', type: LabelItemType.LABEL })
        );
    });

    it('Check hierarchy with 2 levels of groups', () => {
        const labels = [
            getMockedLabel({
                name: 'test1',
                id: 'test1',
                group: 'root 2',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'abc',
                id: 'abc',
                group: `root 2${GROUP_SEPARATOR}subroot`,
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'cde',
                id: 'cde',
                group: `root 2${GROUP_SEPARATOR}subroot`,
                parentLabelId: null,
            }),
        ];
        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);

        expect(result).toHaveLength(1);
        expect(result[0].name).toBe('root 2');
        expect(result[0].relation).toBe(LabelsRelationType.SINGLE_SELECTION);
        expect(result[0].children).toStrictEqual([
            expect.objectContaining({ name: 'test1', type: LabelItemType.LABEL }),
            expect.objectContaining({
                name: 'subroot',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
            }),
        ]);
        expect(result[0].children[1].children).toHaveLength(2);
        expect(getFlattenedGroups(result)).toHaveLength(2);
        expect(getFlattenedLabels(result)).toHaveLength(3);
    });

    it('Check hierarchy with 3 levels of groups', () => {
        const labels = [
            getMockedLabel({
                name: 'test1',
                id: 'test1',
                group: 'root 2',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'abc',
                id: 'abc',
                group: `root 2${GROUP_SEPARATOR}subroot`,
                parentLabelId: 'test1',
            }),
            getMockedLabel({
                name: 'cde',
                id: 'cde',
                group: `root 2${GROUP_SEPARATOR}subroot`,
                parentLabelId: 'test1',
            }),
            getMockedLabel({
                name: '123',
                id: '123',
                group: `root 2${GROUP_SEPARATOR}subroot${GROUP_SEPARATOR}sub`,
                parentLabelId: 'cde',
            }),
        ];
        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);
        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'root 2',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
                children: [
                    expect.objectContaining({
                        name: 'test1',
                        type: LabelItemType.LABEL,
                        group: 'root 2',
                        children: [
                            expect.objectContaining({
                                name: 'subroot',
                                type: LabelItemType.GROUP,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                                children: [
                                    expect.objectContaining({
                                        name: 'abc',
                                        type: LabelItemType.LABEL,
                                        group: `root 2${GROUP_SEPARATOR}subroot`,
                                        children: [],
                                    }),
                                    expect.objectContaining({
                                        name: 'cde',
                                        type: LabelItemType.LABEL,
                                        group: `root 2${GROUP_SEPARATOR}subroot`,
                                        children: [
                                            expect.objectContaining({
                                                name: 'sub',
                                                type: LabelItemType.GROUP,
                                                relation: LabelsRelationType.SINGLE_SELECTION,
                                                children: [
                                                    expect.objectContaining({
                                                        name: '123',
                                                        group: `root 2${GROUP_SEPARATOR}subroot${GROUP_SEPARATOR}sub`,
                                                        type: LabelItemType.LABEL,
                                                    }),
                                                ],
                                            }),
                                        ],
                                    }),
                                ],
                            }),
                        ],
                    }),
                ],
            }),
        ]);
    });

    it('Check hierarchy with 3 levels of groups two root groups', () => {
        const labels = [
            getMockedLabel({
                name: 'label1',
                id: 'label1',
                group: 'root',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'label2',
                id: 'label2',
                group: 'root',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'label3',
                id: 'label3',
                group: 'root',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'test1',
                id: 'test1',
                group: 'root 2',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'abc',
                id: 'abc',
                group: `root 2${GROUP_SEPARATOR}subroot`,
                parentLabelId: 'test1',
            }),
            getMockedLabel({
                name: 'cde',
                id: 'cde',
                group: `root 2${GROUP_SEPARATOR}subroot`,
                parentLabelId: 'test1',
            }),
            getMockedLabel({
                name: '123',
                id: '123',
                group: `root 2${GROUP_SEPARATOR}subroot${GROUP_SEPARATOR}sub`,
                parentLabelId: 'cde',
            }),
        ];
        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);
        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'root',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
                children: [
                    expect.objectContaining({ name: 'label1', group: 'root', type: LabelItemType.LABEL }),
                    expect.objectContaining({ name: 'label2', group: 'root', type: LabelItemType.LABEL }),
                    expect.objectContaining({ name: 'label3', group: 'root', type: LabelItemType.LABEL }),
                ],
            }),
            expect.objectContaining({
                name: 'root 2',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
                children: [
                    expect.objectContaining({
                        name: 'test1',
                        group: 'root 2',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: 'subroot',
                                type: LabelItemType.GROUP,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                                children: [
                                    expect.objectContaining({
                                        name: 'abc',
                                        group: `root 2${GROUP_SEPARATOR}subroot`,
                                        type: LabelItemType.LABEL,
                                    }),
                                    expect.objectContaining({
                                        name: 'cde',
                                        group: `root 2${GROUP_SEPARATOR}subroot`,
                                        type: LabelItemType.LABEL,
                                        children: [
                                            expect.objectContaining({
                                                name: 'sub',
                                                type: LabelItemType.GROUP,
                                                relation: LabelsRelationType.SINGLE_SELECTION,
                                                children: [
                                                    expect.objectContaining({
                                                        name: '123',
                                                        group: `root 2${GROUP_SEPARATOR}subroot${GROUP_SEPARATOR}sub`,
                                                        type: LabelItemType.LABEL,
                                                    }),
                                                ],
                                            }),
                                        ],
                                    }),
                                ],
                            }),
                        ],
                    }),
                ],
            }),
        ]);
    });

    it('Check chain det>cla with one level groups in classification', () => {
        const labels = [
            getMockedLabel({
                name: 'animal',
                id: 'animal',
                group: 'Default group root task',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'Cat',
                id: 'Cat',
                group: `Default group root task${GROUP_SEPARATOR}Kinds`,
                parentLabelId: 'animal',
            }),
            getMockedLabel({
                name: 'Dog',
                id: 'Dog',
                group: `Default group root task${GROUP_SEPARATOR}Kinds`,
                parentLabelId: 'animal',
            }),
        ];
        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);
        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'Default group root task',
                type: LabelItemType.GROUP,
                children: [
                    expect.objectContaining({
                        name: 'animal',
                        group: 'Default group root task',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: 'Kinds',
                                parentLabelId: 'animal',
                                parentName: 'Default group root task',
                                type: LabelItemType.GROUP,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                                children: [
                                    expect.objectContaining({
                                        name: 'Cat',
                                        group: `Default group root task${GROUP_SEPARATOR}Kinds`,
                                        type: LabelItemType.LABEL,
                                    }),
                                    expect.objectContaining({
                                        name: 'Dog',
                                        group: `Default group root task${GROUP_SEPARATOR}Kinds`,
                                        type: LabelItemType.LABEL,
                                    }),
                                ],
                            }),
                        ],
                    }),
                ],
            }),
        ]);
    });

    it('With label hierarchy', () => {
        const labels: ReadonlyArray<Label> = [
            getMockedLabel({
                color: '#c9e649ff',
                group: 'Object',
                id: '62542dff266442022f278e8d',
                name: 'Car',
                behaviour: LABEL_BEHAVIOUR.GLOBAL,
            }),
            getMockedLabel({
                color: '#f7dab3ff',
                group: 'Object',
                id: '62542dff266442022f278e8e',
                name: 'Person',
                behaviour: LABEL_BEHAVIOUR.GLOBAL,
            }),
            getMockedLabel({
                color: '#9b5de5ff',
                group: `Object${GROUP_SEPARATOR}Brand`,
                id: '62542dff266442022f278e8f',
                name: 'Aston Martin',
                behaviour: LABEL_BEHAVIOUR.GLOBAL,
                parentLabelId: '62542dff266442022f278e8d',
            }),
            getMockedLabel({
                color: '#076984ff',
                group: `Object${GROUP_SEPARATOR}Brand`,
                id: '62542dff266442022f278e90',
                name: 'Volvo',
                behaviour: LABEL_BEHAVIOUR.GLOBAL,
                parentLabelId: '62542dff266442022f278e8d',
            }),
        ];
        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);
        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'Object',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
                children: [
                    expect.objectContaining({
                        name: 'Car',
                        group: 'Object',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: 'Brand',
                                type: LabelItemType.GROUP,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                                children: [
                                    expect.objectContaining({
                                        name: 'Aston Martin',
                                        group: `Object${GROUP_SEPARATOR}Brand`,
                                        type: LabelItemType.LABEL,
                                    }),
                                    expect.objectContaining({
                                        name: 'Volvo',
                                        group: `Object${GROUP_SEPARATOR}Brand`,
                                        type: LabelItemType.LABEL,
                                    }),
                                ],
                            }),
                        ],
                    }),
                    expect.objectContaining({ name: 'Person', group: 'Object', type: LabelItemType.LABEL }),
                ],
            }),
        ]);
    });

    it('Hierarchy with multi label directory as label children', () => {
        const labels = [
            getMockedLabel({
                name: 'test1',
                id: 'test1',
                group: 'root',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'abc',
                id: 'abc',
                group: 'root',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'cde',
                id: 'cde',
                group: `root${GROUP_SEPARATOR}123${GROUP_SEPARATOR}cde`,
                parentLabelId: 'test1',
            }),
            getMockedLabel({
                name: '234',
                id: '234',
                group: `root${GROUP_SEPARATOR}123${GROUP_SEPARATOR}234`,
                parentLabelId: 'test1',
            }),
            getMockedLabel({
                name: 'aaa',
                id: 'aaa',
                group: `root${GROUP_SEPARATOR}123${GROUP_SEPARATOR}234${GROUP_SEPARATOR}test`,
                parentLabelId: '234',
            }),
        ];

        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);
        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'root',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
                children: [
                    expect.objectContaining({
                        name: 'test1',
                        group: 'root',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: '123',
                                type: LabelItemType.GROUP,
                                relation: LabelsRelationType.MULTI_SELECTION,
                                children: [
                                    expect.objectContaining({
                                        name: 'cde',
                                        group: `root${GROUP_SEPARATOR}123${GROUP_SEPARATOR}cde`,
                                        type: LabelItemType.LABEL,
                                    }),
                                    expect.objectContaining({
                                        name: '234',
                                        group: `root${GROUP_SEPARATOR}123${GROUP_SEPARATOR}234`,
                                        type: LabelItemType.LABEL,
                                        children: [
                                            expect.objectContaining({
                                                name: 'test',
                                                type: LabelItemType.GROUP,
                                                relation: LabelsRelationType.SINGLE_SELECTION,
                                                children: [
                                                    expect.objectContaining({
                                                        name: 'aaa',
                                                        group: `root${GROUP_SEPARATOR}123${GROUP_SEPARATOR}234${GROUP_SEPARATOR}test`,
                                                        type: LabelItemType.LABEL,
                                                    }),
                                                ],
                                            }),
                                        ],
                                    }),
                                ],
                            }),
                        ],
                    }),
                    expect.objectContaining({ name: 'abc', group: 'root', type: LabelItemType.LABEL }),
                ],
            }),
        ]);
    });

    it('Hierarchy with multi label groups', () => {
        const labels: Label[] = [
            getMockedLabel({
                id: '6260fb73d96dbf56914ea51d',
                name: 'label1',
                color: '#81407bff',
                group: 'group1___label1',
            }),

            getMockedLabel({
                id: '6260fb73d96dbf56914ea51e',
                name: 'label2',
                color: '#d7bc5eff',
                group: 'group1___label2',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea51f',
                name: 'label8',
                color: '#81407bff',
                group: 'group1___label2___group2___label8',
                parentLabelId: '6260fb73d96dbf56914ea51e',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea520',
                name: 'label9',
                color: '#c9e649ff',
                group: 'group1___label2___group2___label9',
                parentLabelId: '6260fb73d96dbf56914ea51e',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea521',
                name: 'label3',
                color: '#cc94daff',
                group: 'group1___label3',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea522',
                name: 'label10',
                color: '#ff5662ff',
                group: 'group1___label3___group3',
                parentLabelId: '6260fb73d96dbf56914ea521',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea523',
                name: 'label11',
                color: '#00a5cfff',
                group: 'group1___label3___group3',
                parentLabelId: '6260fb73d96dbf56914ea521',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea524',
                name: 'label4',
                color: '#5b69ffff',
                group: 'group1___label4',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea525',
                name: 'label5',
                color: '#25a18eff',
                group: 'group4',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea526',
                name: 'label6',
                color: '#f15b85ff',
                group: 'group4',
            }),
            getMockedLabel({
                id: '6260fb73d96dbf56914ea527',
                name: 'label7',
                color: '#26518eff',
                group: 'group4',
            }),
        ];

        expect(fetchLabelsTreeWithGroups(labels, 'all', null, null)).toStrictEqual([
            expect.objectContaining({
                name: 'group1',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.MULTI_SELECTION,
                children: [
                    expect.objectContaining({
                        name: 'label1',
                        group: 'group1___label1',
                        type: LabelItemType.LABEL,
                        children: [],
                    }),
                    expect.objectContaining({
                        name: 'label2',
                        group: 'group1___label2',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: 'group2',
                                type: LabelItemType.GROUP,
                                relation: LabelsRelationType.MULTI_SELECTION,
                                children: [
                                    expect.objectContaining({
                                        name: 'label8',
                                        type: LabelItemType.LABEL,
                                        group: 'group1___label2___group2___label8',
                                        children: [],
                                    }),
                                    expect.objectContaining({
                                        name: 'label9',
                                        type: LabelItemType.LABEL,
                                        group: 'group1___label2___group2___label9',
                                        children: [],
                                    }),
                                ],
                            }),
                        ],
                    }),
                    expect.objectContaining({
                        name: 'label3',
                        group: 'group1___label3',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: 'group3',
                                type: LabelItemType.GROUP,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                                children: [
                                    expect.objectContaining({
                                        name: 'label10',
                                        type: LabelItemType.LABEL,
                                        group: 'group1___label3___group3',
                                        children: [],
                                    }),
                                    expect.objectContaining({
                                        name: 'label11',
                                        type: LabelItemType.LABEL,
                                        group: 'group1___label3___group3',
                                        children: [],
                                    }),
                                ],
                            }),
                        ],
                    }),
                    expect.objectContaining({
                        name: 'label4',
                        group: 'group1___label4',
                        type: LabelItemType.LABEL,
                        children: [],
                    }),
                ],
            }),
            expect.objectContaining({
                name: 'group4',
                type: LabelItemType.GROUP,
                relation: LabelsRelationType.SINGLE_SELECTION,
                children: [
                    expect.objectContaining({
                        name: 'label5',
                        group: 'group4',
                        type: LabelItemType.LABEL,
                        children: [],
                    }),
                    expect.objectContaining({
                        name: 'label6',
                        group: 'group4',
                        type: LabelItemType.LABEL,
                        children: [],
                    }),
                    expect.objectContaining({
                        name: 'label7',
                        group: 'group4',
                        type: LabelItemType.LABEL,
                        children: [],
                    }),
                ],
            }),
        ]);
    });

    it('Hierarchical labels all in the same group', () => {
        const labels = [
            getMockedLabel({
                name: 'Object',
                id: 'object-label',
                group: 'detection task label group',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'Empty Classification',
                id: 'empty-label',
                group: 'default - Classification',
                parentLabelId: 'object-label',
            }),
            getMockedLabel({
                name: 'Animalia',
                id: 'animalia-label',
                group: 'default - Classification',
                parentLabelId: 'object-label',
            }),
            getMockedLabel({
                name: 'Arthropoda',
                id: 'arthropoda-label',
                group: 'default - Classification',
                parentLabelId: 'animalia-label',
            }),
            getMockedLabel({
                name: 'Archanida',
                id: 'archanida-label',
                group: 'default - Classification',
                parentLabelId: 'arthropoda-label',
            }),
            getMockedLabel({
                name: 'Opiliones',
                id: 'opiliones-label',
                group: 'default - Classification',
                parentLabelId: 'archanida-label',
            }),
            getMockedLabel({
                name: 'Araneae',
                id: 'araneae-label',
                group: 'default - Classification',
                parentLabelId: 'archanida-label',
            }),
            getMockedLabel({
                name: 'Insecta',
                id: 'insecta-label',
                group: 'default - Classification',
                parentLabelId: 'arthropoda-label',
            }),
        ];
        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);

        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'detection task label group',
                parentLabelId: null,
                type: LabelItemType.GROUP,
                children: [
                    expect.objectContaining({
                        name: 'Object',
                        group: 'detection task label group',
                        id: 'object-label',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: 'default - Classification',
                                type: LabelItemType.GROUP,
                                children: [
                                    expect.objectContaining({
                                        name: 'Empty Classification',
                                        group: 'default - Classification',
                                        id: 'empty-label',
                                        type: LabelItemType.LABEL,
                                        children: [],
                                    }),
                                    expect.objectContaining({
                                        name: 'Animalia',
                                        group: 'default - Classification',
                                        id: 'animalia-label',
                                        type: LabelItemType.LABEL,
                                        children: [
                                            expect.objectContaining({
                                                name: 'default - Classification',
                                                type: LabelItemType.GROUP,
                                                children: [
                                                    expect.objectContaining({
                                                        name: 'Arthropoda',
                                                        type: LabelItemType.LABEL,
                                                        group: 'default - Classification',
                                                        id: 'arthropoda-label',
                                                        children: [
                                                            expect.objectContaining({
                                                                name: 'default - Classification',
                                                                type: LabelItemType.GROUP,
                                                                children: [
                                                                    expect.objectContaining({
                                                                        name: 'Archanida',
                                                                        type: LabelItemType.LABEL,
                                                                        group: 'default - Classification',
                                                                        id: 'archanida-label',
                                                                        children: [
                                                                            expect.objectContaining({
                                                                                name: 'default - Classification',
                                                                                type: LabelItemType.GROUP,
                                                                                children: [
                                                                                    expect.objectContaining({
                                                                                        name: 'Opiliones',
                                                                                        type: LabelItemType.LABEL,
                                                                                        group: 'default - Classification',
                                                                                        id: 'opiliones-label',
                                                                                        children: [],
                                                                                    }),
                                                                                    expect.objectContaining({
                                                                                        name: 'Araneae',
                                                                                        type: LabelItemType.LABEL,
                                                                                        group: 'default - Classification',
                                                                                        id: 'araneae-label',
                                                                                        children: [],
                                                                                    }),
                                                                                ],
                                                                            }),
                                                                        ],
                                                                    }),
                                                                    expect.objectContaining({
                                                                        name: 'Insecta',
                                                                        type: LabelItemType.LABEL,
                                                                        group: 'default - Classification',
                                                                        id: 'insecta-label',
                                                                        children: [],
                                                                    }),
                                                                ],
                                                            }),
                                                        ],
                                                    }),
                                                ],
                                            }),
                                        ],
                                    }),
                                ],
                            }),
                        ],
                    }),
                ],
            }),
        ]);
    });

    it('Edition of multi selection', () => {
        const labels = [
            getMockedLabel({ name: 'detection', group: 'Default group root task', parentLabelId: null, id: '123123' }),
            getMockedLabel({ name: '123333', group: 'Default group root task___group___123', parentLabelId: '123123' }),
            getMockedLabel({ name: '234', group: 'Default group root task___group___234', parentLabelId: '123123' }),
        ];

        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);

        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'Default group root task',
                type: LabelItemType.GROUP,
                parentLabelId: null,
                children: [
                    expect.objectContaining({
                        name: 'detection',
                        type: LabelItemType.LABEL,
                        parentLabelId: null,
                        children: [
                            expect.objectContaining({
                                name: 'group',
                                type: LabelItemType.GROUP,
                                parentLabelId: '123123',
                                children: [
                                    expect.objectContaining({
                                        name: '123333',
                                        type: LabelItemType.LABEL,
                                        parentLabelId: '123123',
                                        children: [],
                                    }),
                                    expect.objectContaining({
                                        name: '234',
                                        type: LabelItemType.LABEL,
                                        parentLabelId: '123123',
                                        children: [],
                                    }),
                                ],
                            }),
                        ],
                    }),
                ],
            }),
        ]);
    });

    it('detection -> segmentation with one label each', () => {
        const labels = [
            getMockedLabel({
                name: 'animal',
                id: 'animal',
                group: 'Detection labels',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'Cat',
                id: 'Cat',
                group: `Detection labels${GROUP_SEPARATOR}Segmentation labels`,
                parentLabelId: null,
            }),
        ];

        const result = fetchLabelsTreeWithGroups(labels, 'all', null, null);

        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'Detection labels',
                type: LabelItemType.GROUP,
                children: [
                    expect.objectContaining({
                        name: 'animal',
                        type: LabelItemType.LABEL,
                        children: [],
                    }),
                    expect.objectContaining({
                        name: `Segmentation labels`,
                        type: LabelItemType.GROUP,
                        children: [
                            expect.objectContaining({
                                name: 'Cat',
                                type: LabelItemType.LABEL,
                                children: [],
                            }),
                        ],
                    }),
                ],
            }),
        ]);
    });
});

describe('Function fetchLabelsTree', () => {
    it('detection -> segmentation with one label each', () => {
        const labels = [
            getMockedLabel({
                name: 'Animal',
                id: 'animal',
                group: 'Detection labels',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'Cat',
                id: 'Cat',
                group: `Detection labels${GROUP_SEPARATOR}Segmentation labels`,
                parentLabelId: null,
            }),
        ];

        const result = fetchLabelsTree(labels, []);

        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'Animal',
                type: LabelItemType.LABEL,
                children: [],
            }),
            expect.objectContaining({
                name: 'Cat',
                type: LabelItemType.LABEL,
                children: [],
            }),
        ]);
    });

    it('Hierarchical labels all in the same group', () => {
        const labels = [
            getMockedLabel({
                name: 'Object',
                id: 'object-label',
                group: 'detection task label group',
                parentLabelId: null,
            }),
            getMockedLabel({
                name: 'Empty Classification',
                id: 'empty-label',
                group: 'default - Classification',
                parentLabelId: 'object-label',
            }),
            getMockedLabel({
                name: 'Animalia',
                id: 'animalia-label',
                group: 'default - Classification',
                parentLabelId: 'object-label',
            }),
            getMockedLabel({
                name: 'Arthropoda',
                id: 'arthropoda-label',
                group: 'default - Classification',
                parentLabelId: 'animalia-label',
            }),
            getMockedLabel({
                name: 'Archanida',
                id: 'archanida-label',
                group: 'default - Classification',
                parentLabelId: 'arthropoda-label',
            }),
            getMockedLabel({
                name: 'Opiliones',
                id: 'opiliones-label',
                group: 'default - Classification',
                parentLabelId: 'archanida-label',
            }),
            getMockedLabel({
                name: 'Araneae',
                id: 'araneae-label',
                group: 'default - Classification',
                parentLabelId: 'archanida-label',
            }),
            getMockedLabel({
                name: 'Insecta',
                id: 'insecta-label',
                group: 'default - Classification',
                parentLabelId: 'arthropoda-label',
            }),
        ];
        const result = fetchLabelsTree(labels, []);

        expect(result).toStrictEqual([
            expect.objectContaining({
                name: 'Object',
                parentLabelId: null,
                type: LabelItemType.LABEL,
                children: [
                    expect.objectContaining({
                        name: 'Empty Classification',
                        group: 'default - Classification',
                        id: 'empty-label',
                        type: LabelItemType.LABEL,
                        children: [],
                    }),
                    expect.objectContaining({
                        name: 'Animalia',
                        group: 'default - Classification',
                        id: 'animalia-label',
                        type: LabelItemType.LABEL,
                        children: [
                            expect.objectContaining({
                                name: 'Arthropoda',
                                type: LabelItemType.LABEL,
                                group: 'default - Classification',
                                id: 'arthropoda-label',
                                children: [
                                    expect.objectContaining({
                                        name: 'Archanida',
                                        type: LabelItemType.LABEL,
                                        group: 'default - Classification',
                                        id: 'archanida-label',
                                        children: [
                                            expect.objectContaining({
                                                name: 'Opiliones',
                                                type: LabelItemType.LABEL,
                                                group: 'default - Classification',
                                                id: 'opiliones-label',
                                                children: [],
                                            }),
                                            expect.objectContaining({
                                                name: 'Araneae',
                                                type: LabelItemType.LABEL,
                                                group: 'default - Classification',
                                                id: 'araneae-label',
                                                children: [],
                                            }),
                                        ],
                                    }),
                                    expect.objectContaining({
                                        name: 'Insecta',
                                        type: LabelItemType.LABEL,
                                        group: 'default - Classification',
                                        id: 'insecta-label',
                                        children: [],
                                    }),
                                ],
                            }),
                        ],
                    }),
                ],
            }),
        ]);
    });
});
