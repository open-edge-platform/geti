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

import { screen } from '@testing-library/react';

import { DOMAIN } from '../../../core/projects/core.interface';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { HierarchicalTreeView } from './hierarchical-tree-view.component';

describe('HierarchicalTreeView', () => {
    it('Check if new labels are shown on the top - reversed order', async () => {
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
                labels={labels}
                save={jest.fn()}
                addChild={jest.fn()}
                deleteItem={jest.fn()}
                isEditable={false}
                domains={[DOMAIN.CLASSIFICATION]}
                projectLabels={labels}
                treeValidationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        const treeItems = screen.getAllByRole('listitem');
        expect(treeItems[0]).toHaveTextContent('Group 2');
        expect(treeItems[1]).toHaveTextContent('Label 4');
        expect(treeItems[2]).toHaveTextContent('Group');
        expect(treeItems[3]).toHaveTextContent('Label 3');
        expect(treeItems[4]).toHaveTextContent('Label 2');
        expect(treeItems[5]).toHaveTextContent('Label 1');
    });
});
