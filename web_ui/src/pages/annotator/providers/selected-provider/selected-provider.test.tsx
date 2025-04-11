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

import { fireEvent, render, screen } from '@testing-library/react';

import { SelectedProvider, useSelected } from './selected-provider.component';

describe('SelectedProvider', () => {
    const renderApp = (selectedIds: string[]) => {
        const App = () => {
            const { isSelected, addSelected, removeSelected, setSelected } = useSelected();

            return (
                <div>
                    <button onClick={() => addSelected(['id1'])}>Add id1</button>
                    <button onClick={() => addSelected(['id2'])}>Add id2</button>
                    <button onClick={() => removeSelected('id1')}>Remove id1</button>
                    <button onClick={() => setSelected([])}>Remove All</button>
                    <button onClick={() => setSelected(['id2'])}>Deselect All But id2</button>

                    <p data-testid='id1-status'>{isSelected('id1') ? 'Selected' : 'Not Selected'}</p>
                    <p data-testid='id2-status'>{isSelected('id2') ? 'Selected' : 'Not Selected'}</p>
                </div>
            );
        };

        render(
            <SelectedProvider selectedIds={selectedIds}>
                <App />
            </SelectedProvider>
        );
    };

    it('initializes with default selected IDs', () => {
        renderApp(['id1', 'id2']);

        expect(screen.getByTestId('id1-status')).toHaveTextContent('Selected');
        expect(screen.getByTestId('id2-status')).toHaveTextContent('Selected');
    });

    it('selects a value', async () => {
        renderApp([]);

        const id1Status = screen.getByTestId('id1-status');
        expect(id1Status).toHaveTextContent('Not Selected');

        fireEvent.click(screen.getByText('Add id1'));
        fireEvent.click(screen.getByText('Add id1'));
        expect(id1Status).toHaveTextContent('Selected');
    });

    it('removes a value', async () => {
        renderApp(['id1', 'id2']);

        const id1Status = screen.getByTestId('id1-status');
        expect(id1Status).toHaveTextContent('Selected');

        fireEvent.click(screen.getByText('Remove id1'));
        expect(id1Status).toHaveTextContent('Not Selected');
    });

    it('clears all selected values', async () => {
        renderApp(['id1', 'id2']);

        expect(screen.getByTestId('id1-status')).toHaveTextContent('Selected');
        expect(screen.getByTestId('id2-status')).toHaveTextContent('Selected');

        fireEvent.click(screen.getByText('Remove All'));
        expect(screen.getByTestId('id1-status')).toHaveTextContent('Not Selected');
        expect(screen.getByTestId('id2-status')).toHaveTextContent('Not Selected');
    });

    it('keeps only one value selected', async () => {
        renderApp(['id1', 'id2']);

        expect(screen.getByTestId('id1-status')).toHaveTextContent('Selected');
        expect(screen.getByTestId('id2-status')).toHaveTextContent('Selected');

        fireEvent.click(screen.getByText('Deselect All But id2'));
        expect(screen.getByTestId('id1-status')).toHaveTextContent('Not Selected');
        expect(screen.getByTestId('id2-status')).toHaveTextContent('Selected');
    });
});
