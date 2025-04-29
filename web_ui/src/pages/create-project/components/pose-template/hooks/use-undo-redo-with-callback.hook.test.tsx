// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';

import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { useUndoRedoWithCallback } from './use-undo-redo-with-callback.hook';

const initialState = { edges: [], points: [] };
const newState = { edges: [], points: [getMockedKeypointNode()] };

describe('useUndoRedoWithCallback', () => {
    const App = ({ callback }: { callback: () => void }) => {
        const [_value, setValue, undoRedo] = useUndoRedoWithCallback(initialState, callback);

        const updatePoint = () => setValue(newState);

        return (
            <div>
                <button onClick={updatePoint}>Update Points</button>

                <button onClick={() => undoRedo.undo()}>Undo</button>
                <button onClick={() => undoRedo.redo()}>Redo</button>
            </div>
        );
    };

    it('does not trigger the callback without a prior update', async () => {
        const mockedCallback = jest.fn();
        render(<App callback={mockedCallback} />);

        fireEvent.click(screen.getByRole('button', { name: 'Redo' }));
        fireEvent.click(screen.getByRole('button', { name: 'Undo' }));

        expect(mockedCallback).not.toHaveBeenCalled();
    });

    describe('callback calling', () => {
        it('undo', async () => {
            const mockedCallback = jest.fn();
            render(<App callback={mockedCallback} />);

            fireEvent.click(screen.getByRole('button', { name: 'Update Points' }));
            fireEvent.click(screen.getByRole('button', { name: 'Undo' }));

            expect(mockedCallback).toHaveBeenLastCalledWith(initialState);
        });

        it('redo', async () => {
            const mockedCallback = jest.fn();
            render(<App callback={mockedCallback} />);

            fireEvent.click(screen.getByRole('button', { name: 'Update Points' }));
            fireEvent.click(screen.getByRole('button', { name: 'Undo' }));
            fireEvent.click(screen.getByRole('button', { name: 'Redo' }));

            expect(mockedCallback).toHaveBeenLastCalledWith(newState);
        });
    });
});
