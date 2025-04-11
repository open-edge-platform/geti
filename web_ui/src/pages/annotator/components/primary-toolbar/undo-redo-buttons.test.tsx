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

import { useState } from 'react';

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { UndoRedoActions } from '../../core/undo-redo-actions.interface';
import UndoRedoProvider from '../../tools/undo-redo/undo-redo-provider.component';
import { UndoRedoButtons } from './undo-redo-buttons.component';

describe('UndoRedo buttons', () => {
    const App = (mockUndoRedoActions: UndoRedoActions) => {
        const [canUndo, setCanUndo] = useState(mockUndoRedoActions.canUndo);
        const [canRedo, setCanRedo] = useState(mockUndoRedoActions.canRedo);

        return (
            <UndoRedoProvider state={{ ...mockUndoRedoActions, canUndo, canRedo }}>
                <button onClick={() => setCanUndo((prevCanUndo) => !prevCanUndo)}>Toggle undo</button>
                <button onClick={() => setCanRedo((prevCanRedo) => !prevCanRedo)}>Toggle redo</button>
                <UndoRedoButtons isDisabled={false} />
            </UndoRedoProvider>
        );
    };

    it('should disable buttons if undo/redo is false', async () => {
        const mockUndoRedoActions: UndoRedoActions = {
            undo: jest.fn(),
            canUndo: false,
            redo: jest.fn(),
            canRedo: false,
            reset: jest.fn(),
        };

        render(<App {...mockUndoRedoActions} />);

        const undoButton = screen.getByTestId('undo-button');
        const redoButton = screen.getByTestId('redo-button');

        expect(undoButton).toBeDisabled();
        expect(redoButton).toBeDisabled();
    });

    it('calls "undo" and "redo" properly when the user clicks on the buttons', async () => {
        const mockUndoRedoActions = {
            undo: jest.fn(),
            canUndo: true,
            redo: jest.fn(),
            canRedo: true,
            reset: jest.fn(),
        };

        render(<App {...mockUndoRedoActions} />);

        const undoButton = screen.getByTestId('undo-button');
        const redoButton = screen.getByTestId('redo-button');

        fireEvent.click(undoButton);
        expect(mockUndoRedoActions.undo).toHaveBeenCalledTimes(1);

        fireEvent.click(redoButton);
        expect(mockUndoRedoActions.redo).toHaveBeenCalledTimes(1);
    });

    it('does NOT call "undo" and "redo" when the user presses the respective hotkeys if there is no state to undo/redo', async () => {
        const mockUndoRedoActions = {
            undo: jest.fn(),
            canUndo: false,
            redo: jest.fn(),
            canRedo: false,
            reset: jest.fn(),
        };

        render(<App {...mockUndoRedoActions} />);

        fireEvent.keyDown(document.body, { key: 'z', keyCode: 90, ctrlKey: true });

        expect(mockUndoRedoActions.undo).not.toHaveBeenCalled();

        fireEvent.keyDown(document.body, { key: 'y', keyCode: 89, ctrlKey: true });

        expect(mockUndoRedoActions.redo).not.toHaveBeenCalled();
    });

    it('calls "undo" and "redo" correctly when the user presses the respective hotkeys if there is a state to undo/redo', async () => {
        const mockUndoRedoActions = {
            undo: jest.fn(),
            canUndo: true,
            redo: jest.fn(),
            canRedo: false,
            reset: jest.fn(),
        };

        render(<App {...mockUndoRedoActions} />);

        // Random undo/redo sequence to test weird scenarios

        // Undo 3 times
        fireEvent.keyDown(document.body, { key: 'z', keyCode: 90, ctrlKey: true });
        fireEvent.keyDown(document.body, { key: 'z', keyCode: 90, ctrlKey: true });
        fireEvent.keyDown(document.body, { key: 'z', keyCode: 90, ctrlKey: true });
        expect(mockUndoRedoActions.undo).toHaveBeenCalledTimes(3);

        // Disable undo
        fireEvent.click(screen.getByText('Toggle undo'));

        // Verify that 'undo' is not called even if we press the 'undo' shortcut keys
        fireEvent.keyDown(document.body, { key: 'z', keyCode: 90, ctrlKey: true });
        expect(mockUndoRedoActions.undo).not.toHaveBeenCalledTimes(4);

        // Toggle redo
        fireEvent.click(screen.getByText('Toggle redo'));

        // Redo 1 time
        fireEvent.keyDown(document.body, { key: 'y', keyCode: 89, ctrlKey: true });
        expect(mockUndoRedoActions.redo).toHaveBeenCalledTimes(1);

        // Enable undo and undo 1 time
        fireEvent.click(screen.getByText('Toggle undo'));
        fireEvent.keyDown(document.body, { key: 'z', keyCode: 90, ctrlKey: true });
        expect(mockUndoRedoActions.undo).toHaveBeenCalledTimes(4);

        // Disable undo
        fireEvent.click(screen.getByText('Toggle undo'));

        // Redo 2 times
        expect(mockUndoRedoActions.redo).toHaveBeenCalledTimes(1);

        await userEvent.keyboard('{Ctrl>}Y{/Ctrl}');

        expect(mockUndoRedoActions.redo).toHaveBeenCalledTimes(2);

        const redoButton = screen.getByRole('button', { name: 'redo' });
        fireEvent.click(redoButton);
        expect(mockUndoRedoActions.redo).toHaveBeenCalledTimes(3);
    });
});
