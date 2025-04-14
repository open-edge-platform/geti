// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
