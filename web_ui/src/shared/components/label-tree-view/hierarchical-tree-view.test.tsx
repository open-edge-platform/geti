// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';
import { noop } from 'lodash-es';

import { DOMAIN } from '../../../core/projects/core.interface';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { HierarchicalTreeView } from './hierarchical-tree-view.component';

describe('HierarchicalTreeView', () => {
    it('Check if new labels are shown on the top', async () => {
        const labels = [
            getMockedTreeGroup({
                name: 'Group',
                children: [
                    getMockedTreeLabel({ name: 'Label 1' }),
                    getMockedTreeLabel({ name: 'Label 2' }),
                    getMockedTreeLabel({ name: 'Label 3' }),
                ],
            }),
            getMockedTreeGroup({ name: 'Group 2', children: [getMockedTreeLabel({ name: 'Label 4' })] }),
        ];

        render(
            <HierarchicalTreeView
                actions={{ addChild: noop, deleteItem: noop, reorder: noop, save: noop }}
                treeItems={labels}
                isEditable={false}
                domains={[DOMAIN.CLASSIFICATION]}
                projectLabels={labels}
                treeValidationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        const treeItems = screen.getAllByRole('listitem');

        expect(treeItems[0]).toHaveTextContent('Group');
        expect(treeItems[1]).toHaveTextContent('Label 1');
        expect(treeItems[2]).toHaveTextContent('Label 2');
        expect(treeItems[3]).toHaveTextContent('Label 3');
        expect(treeItems[4]).toHaveTextContent('Group 2');
        expect(treeItems[5]).toHaveTextContent('Label 4');
    });
});
