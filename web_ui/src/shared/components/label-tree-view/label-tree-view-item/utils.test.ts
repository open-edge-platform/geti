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

import { LabelItemEditionState } from '../../../../core/labels/label-tree-view.interface';
import { getFlattenedItems } from '../../../../core/labels/utils';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getItemId, setRemovedStateToChildren } from './utils';

describe('setRemovedStateToChildren', () => {
    it('item with no children', () => {
        const mockedLabel = getMockedTreeLabel({ children: [] });
        const result = setRemovedStateToChildren(mockedLabel);
        expect(result).toStrictEqual([]);
    });

    it('label with children', () => {
        const children = [getMockedTreeLabel(), getMockedTreeLabel(), getMockedTreeLabel()];
        const mockedLabel = getMockedTreeLabel({
            children,
        });
        const result = setRemovedStateToChildren(mockedLabel);
        expect(result).toStrictEqual(children.map((current) => ({ ...current, state: LabelItemEditionState.REMOVED })));
    });

    it('group with children', () => {
        const children = [getMockedTreeLabel()];
        const mockedLabel = getMockedTreeGroup({ children });
        const result = setRemovedStateToChildren(mockedLabel);
        expect(result).toStrictEqual(children.map((current) => ({ ...current, state: LabelItemEditionState.REMOVED })));
    });

    it('item with children and grandchildren - REMOVED to all the descendant which are labels', () => {
        const children = [
            getMockedTreeLabel({ children: [getMockedTreeLabel()] }),
            getMockedTreeGroup({ children: [getMockedTreeLabel()] }),
            getMockedTreeLabel(),
        ];
        const mockedLabel = getMockedTreeGroup({ children });
        const result = setRemovedStateToChildren(mockedLabel);

        const flatResult = getFlattenedItems(result);
        expect(flatResult).toHaveLength(5);
        expect(flatResult.filter(({ state }) => state === LabelItemEditionState.REMOVED)).toHaveLength(4);
    });
});

describe('Check label tree item id', () => {
    it('Check group id', () => {
        expect(getItemId(getMockedTreeGroup({ name: 'test', id: 'test' }))).toBe('group-test-group');
    });

    it('Check label id width hierarchical group', () => {
        expect(getItemId(getMockedTreeLabel({ name: 'test', id: 'testId', group: 'test___test2' }))).toBe(
            'group-test2-test-label'
        );
    });

    it('Check label id', () => {
        expect(getItemId(getMockedTreeLabel({ name: 'test', id: 'testId', group: 'test' }))).toBe(
            'group-test-test-label'
        );
    });
});
