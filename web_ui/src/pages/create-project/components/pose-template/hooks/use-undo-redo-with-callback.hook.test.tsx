// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
