// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';

import { UndoRedoActions } from '../../../../annotator/core/undo-redo-actions.interface';
import { TemplatePrimaryToolbar } from './template-primary-toolbar.component';

describe('TemplatePrimaryToolbar', () => {
    const renderApp = (props: Partial<UndoRedoActions>) => {
        const mockUndoRedoActions = {
            undo: jest.fn(),
            redo: jest.fn(),
            canUndo: true,
            canRedo: true,
            reset: jest.fn(),
            ...props,
        };
        render(<TemplatePrimaryToolbar undoRedoActions={mockUndoRedoActions} isHotKeysVisible={true} />);
        return mockUndoRedoActions;
    };

    it('call undo action', () => {
        const { undo } = renderApp({});

        fireEvent.click(screen.getByLabelText('undo'));
        expect(undo).toHaveBeenCalled();
    });

    it('call redo action', () => {
        const { redo } = renderApp({});

        fireEvent.click(screen.getByLabelText('redo'));
        expect(redo).toHaveBeenCalled();
    });

    it('disable undo button when canUndo is false', () => {
        renderApp({ canUndo: false });
        expect(screen.getByLabelText('undo')).toBeDisabled();
    });

    it('disable redo button when canRedo is false', () => {
        renderApp({ canRedo: false });
        expect(screen.getByLabelText('redo')).toBeDisabled();
    });

    describe('hotkeys', () => {
        it('call undo action', () => {
            const { undo } = renderApp({});

            fireEvent.keyDown(document, { key: 'z', keyCode: 90, ctrlKey: true });

            expect(undo).toHaveBeenCalled();
        });

        it('call redo action', () => {
            const { redo } = renderApp({});

            fireEvent.keyDown(document, { key: 'y', keyCode: 89, ctrlKey: true });
            expect(redo).toHaveBeenCalled();
        });
    });
});
