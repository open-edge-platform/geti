// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ExportStatusStateDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';
import { LabelItemEditionState, LabelItemType, LabelTreeItem } from '../../labels/label-tree-view.interface';
import { LABEL_BEHAVIOUR, LabelsRelationType } from '../../labels/label.interface';
import { getEditLabelsPayload, isStateDone, isStateError } from './utils';

describe('Projects hooks utils', () => {
    describe('getEditLabelsPayload', () => {
        describe('when hierarchy', () => {
            it("returns correct parent-child mapping for labels where child's parent id is equal to parent name", () => {
                const labels: LabelTreeItem[] = [
                    {
                        id: 'Group1',
                        name: 'Group1',
                        type: LabelItemType.GROUP,
                        parentLabelId: null,
                        open: true,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                        parentName: null,
                        children: [
                            {
                                id: '6737565966acc5575c413a82',
                                name: 'A',
                                color: '#cc94daff',
                                group: 'Group1',
                                parentLabelId: null,
                                hotkey: '',
                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                isEmpty: false,
                                open: true,
                                children: [],
                                inEditMode: false,
                                type: LabelItemType.LABEL,
                                state: LabelItemEditionState.IDLE,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                            },
                            {
                                id: '6737565966acc5575c413a83',
                                name: 'B',
                                color: '#076984ff',
                                group: 'Group1',
                                parentLabelId: null,
                                hotkey: '',
                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                isEmpty: false,
                                open: true,
                                children: [],
                                inEditMode: false,
                                type: LabelItemType.LABEL,
                                state: LabelItemEditionState.IDLE,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                            },
                        ],
                        inEditMode: false,
                        state: LabelItemEditionState.IDLE,
                    },
                    {
                        name: 'Gz',
                        id: '4451d633-4dfd-415c-b34e-dee77bdfd5b0',
                        parentLabelId: null,
                        parentName: null,
                        open: true,
                        children: [
                            {
                                name: 'Lz',
                                id: '151ac58f-59cc-437a-a168-fd239f3ee5a7',
                                color: '#708541ff',
                                group: 'Gz',
                                parentLabelId: null,
                                open: true,
                                children: [
                                    {
                                        name: 'Gy',
                                        id: 'd895d003-23c2-458f-806e-9cd57ac5f16f',
                                        parentLabelId: '151ac58f-59cc-437a-a168-fd239f3ee5a7',
                                        parentName: 'Gz',
                                        open: true,
                                        children: [
                                            {
                                                name: 'Ly',
                                                id: 'fad68ad0-43f0-4c85-8379-4094cdf937c9',
                                                color: '#f7dab3ff',
                                                group: 'Gz___Gy',
                                                parentLabelId: '151ac58f-59cc-437a-a168-fd239f3ee5a7',
                                                open: true,
                                                children: [],
                                                state: LabelItemEditionState.NEW,
                                                inEditMode: true,
                                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                                type: LabelItemType.LABEL,
                                                relation: LabelsRelationType.SINGLE_SELECTION,
                                                isEmpty: false,
                                            },
                                        ],
                                        inEditMode: true,
                                        relation: LabelsRelationType.SINGLE_SELECTION,
                                        type: LabelItemType.GROUP,
                                        state: LabelItemEditionState.NEW,
                                    },
                                ],
                                state: LabelItemEditionState.NEW,
                                inEditMode: true,
                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                type: LabelItemType.LABEL,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                                isEmpty: false,
                            },
                        ],
                        inEditMode: false,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                        type: LabelItemType.GROUP,
                        state: LabelItemEditionState.NEW,
                    },
                ];
                const relation = LabelsRelationType.MIXED;
                const shouldRevisit = true;
                const expectedLabels = [
                    {
                        id: '6737565966acc5575c413a82',
                        name: 'A',
                        color: '#cc94daff',
                        hotkey: '',
                        group: 'Group1',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        id: '6737565966acc5575c413a83',
                        name: 'B',
                        color: '#076984ff',
                        hotkey: '',
                        group: 'Group1',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        revisitAffectedAnnotations: true,
                        name: 'Lz',
                        color: '#708541ff',
                        group: 'Gz',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        revisitAffectedAnnotations: true,
                        name: 'Ly',
                        color: '#f7dab3ff',
                        group: 'Gz___Gy',
                        parentLabelId: 'Lz',
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                ];
                expect(getEditLabelsPayload(labels, relation, shouldRevisit)).toEqual(expectedLabels);
            });

            it('returns "isDeleted" flag for deleted labels', () => {
                const labels: LabelTreeItem[] = [
                    {
                        id: 'Group1',
                        name: 'Group1',
                        type: LabelItemType.GROUP,
                        parentLabelId: null,
                        open: true,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                        parentName: null,
                        children: [
                            {
                                id: '6737565966acc5575c413a82',
                                name: 'A',
                                color: '#cc94daff',
                                group: 'Group1',
                                parentLabelId: null,
                                hotkey: '',
                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                isEmpty: false,
                                open: true,
                                children: [],
                                inEditMode: false,
                                type: LabelItemType.LABEL,
                                state: LabelItemEditionState.IDLE,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                            },
                            {
                                id: '6737565966acc5575c413a83',
                                name: 'B',
                                color: '#076984ff',
                                group: 'Group1',
                                parentLabelId: null,
                                hotkey: '',
                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                isEmpty: false,
                                open: true,
                                children: [],
                                inEditMode: false,
                                type: LabelItemType.LABEL,
                                state: LabelItemEditionState.IDLE,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                            },
                        ],
                        inEditMode: false,
                        state: LabelItemEditionState.IDLE,
                    },
                    {
                        id: 'Gz',
                        name: 'Gz',
                        type: LabelItemType.GROUP,
                        parentLabelId: null,
                        open: true,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                        parentName: null,
                        children: [
                            {
                                id: '673b0f6c66acc5575c413b33',
                                name: 'Lz',
                                color: '#ff7d00ff',
                                group: 'Gz',
                                parentLabelId: null,
                                hotkey: '',
                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                isEmpty: false,
                                open: true,
                                children: [
                                    {
                                        id: 'Gz___Gy',
                                        name: 'Gy',
                                        type: LabelItemType.GROUP,
                                        parentLabelId: '673b0f6c66acc5575c413b33',
                                        open: true,
                                        relation: LabelsRelationType.SINGLE_SELECTION,
                                        parentName: 'Gz',
                                        children: [
                                            {
                                                id: '673b0f6c66acc5575c413b34',
                                                name: 'Ly',
                                                color: '#548fadff',
                                                group: 'Gz___Gy',
                                                parentLabelId: '673b0f6c66acc5575c413b33',
                                                hotkey: '',
                                                behaviour: LABEL_BEHAVIOUR.LOCAL,
                                                isEmpty: false,
                                                open: true,
                                                children: [],
                                                inEditMode: false,
                                                type: LabelItemType.LABEL,
                                                state: LabelItemEditionState.REMOVED,
                                                relation: LabelsRelationType.SINGLE_SELECTION,
                                            },
                                        ],
                                        inEditMode: false,
                                        state: LabelItemEditionState.REMOVED,
                                    },
                                ],
                                inEditMode: false,
                                type: LabelItemType.LABEL,
                                state: LabelItemEditionState.REMOVED,
                                relation: LabelsRelationType.SINGLE_SELECTION,
                            },
                        ],
                        inEditMode: false,
                        state: LabelItemEditionState.IDLE,
                    },
                ];
                const expectedLabels = [
                    {
                        id: '6737565966acc5575c413a82',
                        name: 'A',
                        color: '#cc94daff',
                        hotkey: '',
                        group: 'Group1',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        id: '6737565966acc5575c413a83',
                        name: 'B',
                        color: '#076984ff',
                        hotkey: '',
                        group: 'Group1',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        id: '673b0f6c66acc5575c413b33',
                        name: 'Lz',
                        color: '#ff7d00ff',
                        hotkey: '',
                        group: 'Gz',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isDeleted: true,
                        isEmpty: false,
                    },
                    {
                        id: '673b0f6c66acc5575c413b34',
                        name: 'Ly',
                        color: '#548fadff',
                        hotkey: '',
                        group: 'Gz___Gy',
                        parentLabelId: '673b0f6c66acc5575c413b33',
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isDeleted: true,
                        isEmpty: false,
                    },
                ];
                const relation = LabelsRelationType.MIXED;

                expect(getEditLabelsPayload(labels, relation)).toEqual(expectedLabels);
            });
        });

        describe('when non-hierarchy', () => {
            it('returns correct mapping', () => {
                const labels: LabelTreeItem[] = [
                    {
                        id: '67322784b45e5d82904dbced',
                        name: 'alice',
                        color: '#80e9afff',
                        group: 'Detection Task Labels',
                        parentLabelId: null,
                        hotkey: '',
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                        open: true,
                        children: [],
                        inEditMode: false,
                        type: LabelItemType.LABEL,
                        state: LabelItemEditionState.IDLE,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                    {
                        id: '6db63530-b8de-486a-82da-acf15bd8e541',
                        name: 'obc',
                        color: '#81407bff',
                        group: 'Detection labels',
                        parentLabelId: null,
                        hotkey: '',
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                        open: true,
                        children: [],
                        inEditMode: false,
                        type: LabelItemType.LABEL,
                        state: LabelItemEditionState.NEW,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                    {
                        name: 'acd',
                        id: '6db63530-b8de-486a-82da-acf15bd8e540',
                        color: '#9d3b1aff',
                        group: 'Detection labels',
                        parentLabelId: null,
                        open: true,
                        children: [],
                        state: LabelItemEditionState.NEW,
                        inEditMode: false,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        type: LabelItemType.LABEL,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                        isEmpty: false,
                    },
                ];
                const relation = LabelsRelationType.SINGLE_SELECTION;
                const expectedLabels = [
                    {
                        id: '67322784b45e5d82904dbced',
                        name: 'alice',
                        color: '#80e9afff',
                        hotkey: '',
                        group: 'Detection Task Labels',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        revisitAffectedAnnotations: false,
                        name: 'obc',
                        color: '#81407bff',
                        hotkey: '',
                        group: 'Detection labels',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        revisitAffectedAnnotations: false,
                        name: 'acd',
                        color: '#9d3b1aff',
                        group: 'Detection labels',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                ];

                expect(getEditLabelsPayload(labels, relation)).toEqual(expectedLabels);
            });

            it('returns "isDeleted" flag for deleted labels', () => {
                const labels: LabelTreeItem[] = [
                    {
                        id: '67322784b45e5d82904dbced',
                        name: 'alice',
                        color: '#80e9afff',
                        group: 'Detection Task Labels',
                        parentLabelId: null,
                        hotkey: '',
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                        open: true,
                        children: [],
                        inEditMode: false,
                        type: LabelItemType.LABEL,
                        state: LabelItemEditionState.IDLE,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                    {
                        id: '673b126766acc5575c413b44',
                        name: 'obc',
                        color: '#81407bff',
                        group: 'Detection labels',
                        parentLabelId: null,
                        hotkey: '',
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                        open: true,
                        children: [],
                        inEditMode: false,
                        type: LabelItemType.LABEL,
                        state: LabelItemEditionState.REMOVED,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    },
                    {
                        name: 'acd',
                        id: '673b127366acc5575c413b50',
                        color: '#9d3b1aff',
                        group: 'Detection labels',
                        parentLabelId: null,
                        open: true,
                        children: [],
                        state: LabelItemEditionState.REMOVED,
                        inEditMode: false,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        type: LabelItemType.LABEL,
                        relation: LabelsRelationType.SINGLE_SELECTION,
                        isEmpty: false,
                    },
                ];
                const relation = LabelsRelationType.SINGLE_SELECTION;
                const expectedLabels = [
                    {
                        id: '67322784b45e5d82904dbced',
                        name: 'alice',
                        color: '#80e9afff',
                        hotkey: '',
                        group: 'Detection Task Labels',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                    },
                    {
                        id: '673b126766acc5575c413b44',
                        name: 'obc',
                        color: '#81407bff',
                        hotkey: '',
                        group: 'Detection labels',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                        isDeleted: true,
                    },
                    {
                        id: '673b127366acc5575c413b50',
                        name: 'acd',
                        color: '#9d3b1aff',
                        group: 'Detection labels',
                        parentLabelId: null,
                        behaviour: LABEL_BEHAVIOUR.LOCAL,
                        isEmpty: false,
                        isDeleted: true,
                    },
                ];

                expect(getEditLabelsPayload(labels, relation)).toEqual(expectedLabels);
            });
        });
    });

    it('isStateDone', () => {
        expect(isStateDone(undefined)).toBe(false);
        expect(isStateDone(ExportStatusStateDTO.ERROR)).toBe(false);
        expect(isStateDone(ExportStatusStateDTO.EXPORTING)).toBe(false);
        expect(isStateDone(ExportStatusStateDTO.STARTING)).toBe(false);
        expect(isStateDone(ExportStatusStateDTO.ZIPPING)).toBe(false);
        expect(isStateDone(ExportStatusStateDTO.DONE)).toBe(true);
    });

    it('isStateError', () => {
        expect(isStateError(undefined)).toBe(false);
        expect(isStateError(ExportStatusStateDTO.ERROR)).toBe(true);
        expect(isStateError(ExportStatusStateDTO.EXPORTING)).toBe(false);
        expect(isStateError(ExportStatusStateDTO.STARTING)).toBe(false);
        expect(isStateError(ExportStatusStateDTO.ZIPPING)).toBe(false);
        expect(isStateError(ExportStatusStateDTO.DONE)).toBe(false);
    });
});
