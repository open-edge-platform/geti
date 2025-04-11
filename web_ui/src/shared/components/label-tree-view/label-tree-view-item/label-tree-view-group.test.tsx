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

import { getMockedTreeGroup } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { LabelTreeViewGroup } from './label-tree-view-group.component';

describe('LabelTreeViewGroup', () => {
    const item = getMockedTreeGroup({ name: 'Color', id: 'color-group' });

    it('Check if edition mode is properly displayed', async () => {
        render(
            <LabelTreeViewGroup
                item={item}
                savedItem={item}
                newTree={false}
                onOpenClickHandler={jest.fn()}
                flatListProjectItems={[]}
                isOpen={true}
                save={jest.fn()}
                inEditionMode={true}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        expect(screen.getByRole('textbox', { name: 'Label group name' })).toBeInTheDocument();
    });
});
