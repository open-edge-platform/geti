// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';

import { ThemeProvider } from '../../../../../theme/theme-provider.component';
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
        expect(handleMenuAction).toHaveBeenCalledWith(items[0].children[0].title);
        expect(handleClose).toBeCalled();
    });
});
