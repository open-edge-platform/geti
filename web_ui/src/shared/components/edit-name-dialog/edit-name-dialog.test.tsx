// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender } from '../../../test-utils/required-providers-render';
import { EditNameDialog } from './edit-name-dialog.component';

const mockOnAction = jest.fn();
const mockClose = jest.fn();
const mockOverlayTriggerState = {
    isOpen: true,
    setOpen: jest.fn(),
    open: jest.fn(),
    close: mockClose,
    toggle: jest.fn(),
};

describe('EditNameDialog', () => {
    it('calls onAction with the correct value', () => {
        providersRender(
            <EditNameDialog
                title={'dataset name'}
                triggerState={mockOverlayTriggerState}
                onAction={mockOnAction}
                defaultName='some dataset'
                names={[]}
            />
        );

        const input = screen.getByRole('textbox', { name: 'Dataset name' });
        const confirmButton = screen.getByRole('button', {
            name: /confirm/i,
        });

        fireEvent.change(input, { target: { value: 'Update name' } });
        fireEvent.click(confirmButton);

        expect(mockOnAction).toHaveBeenCalledWith('Update name');

        fireEvent.change(input, { target: { value: '' } });

        // Also trims any empty space
        fireEvent.change(input, { target: { value: 'newName           ' } });
        fireEvent.click(confirmButton);

        expect(mockOnAction).toHaveBeenCalledWith('newName');
    });

    it('does NOT call onAction if the newName is the same as oldName', () => {
        providersRender(
            <EditNameDialog
                title={'dataset name'}
                triggerState={mockOverlayTriggerState}
                onAction={mockOnAction}
                defaultName='some dataset'
                names={[]}
            />
        );

        const input = screen.getByRole('textbox', { name: 'Dataset name' });
        const confirmButton = screen.getByRole('button', {
            name: /confirm/i,
        });

        fireEvent.change(input, { target: { value: 'some dataset' } });
        fireEvent.click(confirmButton);

        expect(mockOnAction).not.toHaveBeenCalledWith();
    });

    it('does NOT call onAction if the newName is empty, confirm button should be disabled', () => {
        providersRender(
            <EditNameDialog
                title={'dataset name'}
                triggerState={mockOverlayTriggerState}
                onAction={mockOnAction}
                defaultName='some dataset'
                names={[]}
            />
        );

        const input = screen.getByRole('textbox', { name: 'Dataset name' });
        const confirmButton = screen.getByRole('button', {
            name: /confirm/i,
        });

        fireEvent.change(input, { target: { value: '' } });
        fireEvent.click(confirmButton);

        expect(mockOnAction).not.toHaveBeenCalledWith();
        expect(confirmButton).toBeDisabled();
    });

    it('should show error message when entered name already exists, confirm button should be disabled', () => {
        const existingName = 'dataset 1';

        providersRender(
            <EditNameDialog
                title={'dataset name'}
                triggerState={mockOverlayTriggerState}
                onAction={mockOnAction}
                defaultName='some dataset'
                names={[existingName]}
            />
        );

        const input = screen.getByRole('textbox', { name: 'Dataset name' });
        const confirmButton = screen.getByRole('button', {
            name: /confirm/i,
        });

        fireEvent.change(input, { target: { value: existingName } });
        fireEvent.click(confirmButton);

        expect(screen.getByText('Dataset name must be unique')).toBeInTheDocument();
        expect(mockOnAction).not.toHaveBeenCalledWith();
        expect(confirmButton).toBeDisabled();
    });
});
