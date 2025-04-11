// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';
import noop from 'lodash/noop';

import { providersRender } from '../../../test-utils/required-providers-render';
import { ListItemGrid } from './list-item-grid.component';

describe('ListItemGrid', () => {
    it('displays the ListMenu component when hovered over', () => {
        const menuText = 'list menu';

        providersRender(
            <ListItemGrid
                id={'test'}
                isLast={false}
                isSelected={false}
                isDragging={false}
                ariaLabel={'list item test'}
                onHoverEnd={noop}
                onHoverStart={noop}
            >
                <ListItemGrid.ListMenu>
                    <p>{menuText}</p>
                </ListItemGrid.ListMenu>
            </ListItemGrid>
        );

        expect(screen.queryByText(menuText)).not.toBeInTheDocument();

        fireEvent.mouseEnter(screen.getByRole('listitem'));
        expect(screen.getByText(menuText)).toBeVisible();
    });
});
