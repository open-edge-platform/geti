// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { fireEvent, render, screen } from '@testing-library/react';

import { CursorContextMenu, CursorContextMenuProps, X_PADDING } from './cursor-context-menu.component';

describe('CursorContextMenu', () => {
    const renderApp = ({
        onOpen = jest.fn(),
        isValidTrigger = jest.fn(),
        isOpen = false,
        children = <div>Menu Content</div>,
    }: Partial<CursorContextMenuProps>) => {
        const App = () => {
            const triggerRef = useRef<HTMLButtonElement>(null);
            return (
                <>
                    <button ref={triggerRef}>trigger</button>
                    <CursorContextMenu
                        onOpen={onOpen}
                        isOpen={isOpen}
                        isValidTrigger={isValidTrigger}
                        triggerRef={triggerRef}
                    >
                        {children}
                    </CursorContextMenu>
                </>
            );
        };
        render(<App />);
    };

    it('should not render the menu when isOpen is false', () => {
        renderApp({ isOpen: false });
        expect(screen.queryByText('Menu Content')).not.toBeInTheDocument();
    });

    it('should not open the menu if isValidTrigger returns false', () => {
        const mockOnOpen = jest.fn();
        renderApp({ isOpen: false, onOpen: mockOnOpen, isValidTrigger: () => false });

        const triggerElement = screen.getByRole('button', { name: 'trigger' });
        fireEvent.contextMenu(triggerElement, { clientX: 100, clientY: 150 });

        expect(mockOnOpen).not.toHaveBeenCalled();
    });

    it('positions the menu at the cursor position on context menu event', () => {
        const mockOnOpen = jest.fn();
        renderApp({ isOpen: true, onOpen: mockOnOpen, isValidTrigger: () => true });

        const position = { clientX: 100, clientY: 150 };
        const triggerElement = screen.getByRole('button', { name: 'trigger' });
        fireEvent.contextMenu(triggerElement, position);

        const container = screen.getByTestId('position container');

        expect(mockOnOpen).toHaveBeenCalled();
        expect(container.style.top).toBe(`${position.clientY}px`);
        expect(container.style.left).toBe(`${position.clientX + X_PADDING}px`);

        expect(screen.getByText('Menu Content')).toBeVisible();
    });
});
