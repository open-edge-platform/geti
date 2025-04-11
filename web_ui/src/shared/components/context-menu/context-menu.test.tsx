// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, render, screen } from '@testing-library/react';

import { ThemeProvider } from '../../../theme/theme-provider.component';
import { ContextMenu } from './context-menu.component';

describe('ContextMenu', () => {
    beforeEach(() => {
        jest.restoreAllMocks();
    });

    const handleClose = jest.fn();
    const handleMenuAction = jest.fn();
    const ariaLabel = 'Test label';
    const items = [{ id: 'Test', children: [{ title: 'Test', icon: <></> }] }];
    const menuPosition = { top: 0, left: 0 };
    const handleContextPosition = jest.fn();

    it('render context menu items properly', () => {
        render(
            <ThemeProvider>
                <ContextMenu
                    isVisible
                    handleClose={handleClose}
                    handleMenuAction={handleMenuAction}
                    ariaLabel={ariaLabel}
                    menuItems={items}
                    menuPosition={menuPosition}
                    getContextMenuPosition={handleContextPosition}
                />
            </ThemeProvider>
        );

        expect(screen.getByLabelText(ariaLabel)).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: items[0].children[0].title })).toBeInTheDocument();
    });

    it('not renders the menu', () => {
        render(
            <ThemeProvider>
                <ContextMenu
                    isVisible={false}
                    handleClose={handleClose}
                    handleMenuAction={handleMenuAction}
                    ariaLabel={ariaLabel}
                    menuItems={items}
                    menuPosition={menuPosition}
                    getContextMenuPosition={handleContextPosition}
                />
            </ThemeProvider>
        );

        expect(screen.queryByLabelText(ariaLabel)).not.toBeInTheDocument();
    });

    it('should invoke handleClose method when menu item was selected', () => {
        render(
            <ThemeProvider>
                <ContextMenu
                    isVisible
                    handleClose={handleClose}
                    handleMenuAction={handleMenuAction}
                    ariaLabel={ariaLabel}
                    menuItems={items}
                    menuPosition={menuPosition}
                    getContextMenuPosition={handleContextPosition}
                />
            </ThemeProvider>
        );

        fireEvent.click(screen.getByRole('menuitem', { name: items[0].children[0].title }));
        expect(handleMenuAction).toBeCalledWith(items[0].children[0].title);
        expect(handleClose).toBeCalled();
    });
});
