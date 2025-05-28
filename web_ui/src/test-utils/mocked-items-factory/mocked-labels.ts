// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeGroupProps,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../../core/labels/label-tree-view.interface';
import { Label, LABEL_BEHAVIOUR } from '../../core/labels/label.interface';
import {
    AdvancedFilterOptions,
    SearchOptionsRule,
    SearchRuleField,
    SearchRuleOperator,
} from '../../core/media/media-filter.interface';

const mockedLabel: Label = {
    id: 'label-1',
    name: 'label-1',
    group: 'group-1',
    color: 'blue',
    parentLabelId: null,
    hotkey: undefined,
    behaviour: LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL,
    isEmpty: false,
    isBackground: false,
};

export const getMockedLabel = (label?: Partial<Label> & { isExclusive?: boolean }): Label => {
    const behaviour = label?.behaviour ?? (label?.isExclusive ? LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.EXCLUSIVE : 0);

    return { ...mockedLabel, ...label, behaviour };
};

export const labels: Label[] = [
    getMockedLabel({
        id: 'card',
        color: '#00ff00',
        name: 'card',
        group: 'card-group',
        hotkey: 'ctrl+1',
        behaviour: LABEL_BEHAVIOUR.LOCAL,
    }),

    // Colors
    getMockedLabel({
        id: 'black',
        color: '#00ffff',
        name: 'black',
        group: 'color',
        parentLabelId: 'card',
        hotkey: 'ctrl+2',
    }),
    getMockedLabel({
        id: 'red',
        color: '#00ffff',
        name: 'red',
        group: 'color',
        parentLabelId: 'card',
        hotkey: 'ctrl+3',
    }),

    // Suits
    getMockedLabel({ id: '♥', color: '#00ffff', name: '♥', group: 'suit', parentLabelId: 'red', hotkey: 'ctrl+4' }),
    getMockedLabel({ id: '♦', color: '#00ffff', name: '♦', group: 'suit', parentLabelId: 'red', hotkey: 'ctrl+5' }),
    getMockedLabel({ id: '♠', color: '#00ffff', name: '♠', group: 'suit', parentLabelId: 'black', hotkey: 'ctrl+6' }),
    getMockedLabel({ id: '♣', color: '#00ffff', name: '♣', group: 'suit', parentLabelId: 'black', hotkey: 'ctrl+7' }),

    // Values
    getMockedLabel({ id: '1', color: '#000000', name: '1', group: 'value', parentLabelId: 'card', hotkey: 'ctrl+8' }),
    getMockedLabel({ id: '2', color: '#000000', name: '2', group: 'value', parentLabelId: 'card', hotkey: 'ctrl+9' }),
    getMockedLabel({ id: '3', color: '#000000', name: '3', group: 'value', parentLabelId: 'card', hotkey: 'alt+1' }),
    getMockedLabel({ id: '4', color: '#000000', name: '4', group: 'value', parentLabelId: 'card', hotkey: 'alt+2' }),
];

export const getMockedLabels = (quantity: number, hotkeys?: string[]): Label[] => {
    const mockedLabels = [];

    for (let i = 1; i <= quantity; ++i) {
        const hotkey = hotkeys && hotkeys.length >= i ? hotkeys[i - 1] : '';
        mockedLabels.push(getMockedLabel({ id: i.toString(), name: `test-${i}`, hotkey }));
    }

    return mockedLabels;
};

export const getMockedTreeLabel = (label?: Partial<LabelTreeItem>): LabelTreeLabelProps => {
    return getMockedTreeItem({ ...label, type: LabelItemType.LABEL }) as LabelTreeLabelProps;
};

export const getMockedTreeGroup = (label?: Partial<LabelTreeItem>): LabelTreeGroupProps => {
    return getMockedTreeItem({ ...label, type: LabelItemType.GROUP }) as LabelTreeGroupProps;
};

const getMockedTreeItem = (item?: Partial<LabelTreeItem>): LabelTreeItem => {
    return {
        ...mockedLabel,
        open: false,
        inEditMode: false,
        children: [],
        state: LabelItemEditionState.IDLE,
        ...item,
        id: item?.id || item?.name || mockedLabel.id,
    } as LabelTreeItem;
};

export const mockedLongLabels = [
    getMockedLabel({
        id: '1',
        name: 'test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test_test',
    }),
    getMockedLabel({
        id: '2',
        name: 'test test test test test test test test test test test test test test test test test test test test',
    }),
    getMockedLabel({
        id: '3',
        name:
            'test test test test test test test test test test test test test test test test test test test ' +
            'test test test test test test test test test test test test test test test test test test test test ' +
            'test test test test test test test test test',
    }),
];

export const MOCKED_HIERARCHY: LabelTreeItem[] = [
    getMockedTreeGroup({
        name: 'Animal',
        children: [
            getMockedTreeLabel({ name: 'Cat' }),
            getMockedTreeLabel({
                name: 'Dog',
                children: [
                    getMockedTreeGroup({
                        name: 'Color',
                        children: [
                            getMockedTreeLabel({ name: 'White' }),
                            getMockedTreeLabel({ name: 'Black' }),
                            getMockedTreeLabel({ name: 'Mixed' }),
                        ],
                    }),
                ],
            }),
            getMockedTreeLabel({ name: 'Hamster' }),
        ],
    }),
];

export const mockFilterOptions = (rules: SearchOptionsRule[]): AdvancedFilterOptions => {
    const mockRules = rules ?? {
        id: '123',
        field: SearchRuleField.MediaUploadDate,
        operator: SearchRuleOperator.Less,
        value: '2020-01-01T00:00:00+01:00',
    };
    return {
        condition: 'and',
        rules: mockRules,
    };
};
