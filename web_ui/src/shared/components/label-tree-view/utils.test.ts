// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../core/labels/label.interface';
import { getFlattenedGroups } from '../../../core/labels/utils';
import { DISTINCT_COLORS } from '../../../pages/create-project/components/distinct-colors';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import {
    checkIfItemWasChanged,
    getEditedItem,
    getEditedItemState,
    getLabelsWithAddedChild,
    getNextColor,
    getTreeWithUpdatedItem,
} from './utils';

describe('labelTreeView utils', () => {
    it('getNextColor - one color is not used - function returns that color', () => {
        const result = getNextColor([
            getMockedTreeLabel({ color: DISTINCT_COLORS[0] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[1] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[2] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[3] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[4] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[5] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[6] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[7] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[8] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[9] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[10] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[11] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[12] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[13] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[14] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[15] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[16] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[17] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[18] }),
            getMockedTreeLabel({ color: DISTINCT_COLORS[19] }),
        ]);
        expect(DISTINCT_COLORS).toHaveLength(21);
        expect(result).toBe(DISTINCT_COLORS[20]);
    });

    it('getNextColor - one color is used - function returns other color among DISTINCT_COLORS', () => {
        const result = getNextColor([getMockedTreeLabel({ color: DISTINCT_COLORS[10] })]);
        expect(DISTINCT_COLORS.includes(result)).toBeTruthy();
        expect(result).not.toBe(DISTINCT_COLORS[10]);
    });
});

describe('getLabelWithEdited function', () => {
    it('Change name of single selection project label', () => {
        const label: LabelTreeItem = getMockedTreeLabel({
            name: 'cat',
            group: 'default',
            relation: LabelsRelationType.SINGLE_SELECTION,
        });
        const label2: LabelTreeItem = getMockedTreeLabel({
            name: 'dog',
            group: 'default',
            relation: LabelsRelationType.SINGLE_SELECTION,
        });
        const labelsTree = [label, label2];
        const result = getTreeWithUpdatedItem(labelsTree, label.id, {
            ...label,
            name: 'changed name',
            state: LabelItemEditionState.CHANGED,
        });

        expect(result).toHaveLength(2);
        expect((result[0] as LabelTreeLabelProps).group).toBe('default');
        expect(result[0].name).toBe('changed name');
        expect(result[1]).toStrictEqual(label2);
    });

    it('Change name of multi selection project label', () => {
        const label: LabelTreeItem = getMockedTreeLabel({
            name: 'cat',
            group: 'cat',
            relation: LabelsRelationType.MULTI_SELECTION,
        });
        const label2: LabelTreeItem = getMockedTreeLabel({
            name: 'dog',
            group: 'dog',
            relation: LabelsRelationType.MULTI_SELECTION,
        });
        const label3: LabelTreeItem = getMockedTreeLabel({
            name: 'hamster',
            group: 'hamster',
            relation: LabelsRelationType.MULTI_SELECTION,
        });
        const labelsTree = [label, label2, label3];
        const result = getTreeWithUpdatedItem(labelsTree, label2.id, {
            ...label2,
            name: 'changed name',
            state: LabelItemEditionState.CHANGED,
        });

        expect(result).toHaveLength(3);
        expect((result[1] as LabelTreeLabelProps).group).toBe('dog');
        expect(result[1].name).toBe('changed name');
        expect(result[0]).toStrictEqual(label);
        expect(result[2]).toStrictEqual(label3);
    });
});

describe('Check item id', () => {
    it('getUpdatedItem - label in edit mode and IDLE - should keep id,change state to CHANGED ', () => {
        const mockedLabel = getMockedTreeLabel({ name: 'test', id: '12345', state: LabelItemEditionState.IDLE });
        const label = getEditedItem(mockedLabel, { ...mockedLabel, name: '123456' });

        expect(label.id).toBe(mockedLabel.id);
        expect(label.state).toBe(LabelItemEditionState.CHANGED);
    });

    it('getUpdatedItem - label in edit mode and IDLE - nothing changed - state should stay', () => {
        const mockedLabel = getMockedTreeLabel({ name: 'test', id: '12345', state: LabelItemEditionState.IDLE });
        const label = getEditedItem(mockedLabel, mockedLabel);

        expect(label.id).toBe(mockedLabel.id);
        expect(label.state).toBe(LabelItemEditionState.IDLE);
    });

    it('getUpdatedItem - label NEW - should change id and keep state ', () => {
        const mockedLabel = getMockedTreeLabel({ name: 'test', id: '12345', state: LabelItemEditionState.NEW });
        const label = getEditedItem(mockedLabel, mockedLabel);

        expect(label.id).toBe(mockedLabel.id);
        expect(label.state).toBe(LabelItemEditionState.NEW);
    });

    it('getUpdatedItem - group not in edit mode and NEW - should change id, keep state and set inEditMode to false,update child parentLabelId and relation', () => {
        const mockedGroup = getMockedTreeGroup({
            name: 'test',
            id: 'test-group-id',
            state: LabelItemEditionState.NEW,
            relation: LabelsRelationType.MULTI_SELECTION,
            children: [
                getMockedTreeLabel({
                    name: 'child',
                    id: 'child-label',
                    parentLabelId: 'test-group-id',
                    relation: LabelsRelationType.SINGLE_SELECTION,
                }),
            ],
        });
        const label = getEditedItem(mockedGroup, mockedGroup);

        expect(label).toStrictEqual(
            expect.objectContaining({
                inEditMode: false,
                id: 'test-group-id',
                state: LabelItemEditionState.NEW,
                relation: LabelsRelationType.MULTI_SELECTION,
                children: [
                    expect.objectContaining({
                        name: 'child',
                        parentLabelId: 'test-group-id',
                        relation: LabelsRelationType.MULTI_SELECTION,
                    }),
                ],
            })
        );
    });
});

describe('getLabelsWithAddedChild', () => {
    it("Get group name if there is group named 'group' - next default should be 'Group 2'", () => {
        const labelsTree = [
            getMockedTreeGroup({ name: 'group', children: [getMockedTreeLabel({ name: 'Label 1', id: 'label-1' })] }),
        ];

        const updatedTree = getLabelsWithAddedChild(labelsTree, labelsTree, 'label-1', 'group', LabelItemType.GROUP);
        expect(getFlattenedGroups(updatedTree).map(({ name }) => name)).toStrictEqual(['group', 'Group 2']);
    });
});

describe('getEditedItemState', () => {
    it('New added item has state NEW - new state is NEW', () => {
        expect(getEditedItemState(true, false, LabelItemEditionState.NEW)).toBe(LabelItemEditionState.NEW);
    });

    it('Item not changed has state IDLE - new state is IDLE', () => {
        expect(getEditedItemState(false, false, LabelItemEditionState.IDLE)).toBe(LabelItemEditionState.IDLE);
    });

    it('Edited item has state IDLE - new state is CHANGED', () => {
        expect(getEditedItemState(false, true, LabelItemEditionState.IDLE)).toBe(LabelItemEditionState.CHANGED);
    });

    it('Edited item has state REMOVED - new state is CHANGED', () => {
        expect(getEditedItemState(false, true, LabelItemEditionState.REMOVED)).toBe(LabelItemEditionState.CHANGED);
    });

    it('Not edited item has state REMOVED - new state is REMOVED', () => {
        expect(getEditedItemState(false, false, LabelItemEditionState.REMOVED)).toBe(LabelItemEditionState.REMOVED);
    });

    it('Not changed label has state CHANGED - new state is IDLE', () => {
        expect(getEditedItemState(false, false, LabelItemEditionState.CHANGED)).toBe(LabelItemEditionState.IDLE);
    });
});

describe('Tests of checkIfItemWasChanged function', () => {
    it('Changed item has state CHANGED after edition', () => {
        const item = getMockedTreeLabel({ name: 'Test' });
        const editedItem = { ...item, name: 'Test 2' };

        expect(checkIfItemWasChanged(editedItem, item)).toBeTruthy();
    });

    it('Not changed item has state IDLE after edition', () => {
        const item = getMockedTreeLabel({ name: 'Test' });
        const editedItem = { ...item };

        expect(checkIfItemWasChanged(editedItem, item)).toBeFalsy();
    });
});
