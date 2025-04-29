// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';

import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { SelectableLabelTag } from './selectable-label-tag.component';

describe('Selectable label tag', () => {
    it('should render correctly', () => {
        const mockHandleChange = jest.fn();
        const mockLabel = getMockedLabel({ name: 'label 1' });

        render(
            <SelectableLabelTag
                value={mockLabel.name}
                label={mockLabel}
                handleOptionChange={mockHandleChange}
                selectedOption={mockLabel.name}
            />
        );

        expect(screen.getByText(mockLabel.name)).toBeInTheDocument();
    });

    it('should trigger callback correctly', () => {
        const mockHandleChange = jest.fn();
        const mockLabel = getMockedLabel({ name: 'label 2' });

        render(
            <SelectableLabelTag
                value={mockLabel.name}
                label={mockLabel}
                handleOptionChange={mockHandleChange}
                selectedOption={mockLabel.name}
            />
        );

        const tag = screen.getByText(mockLabel.name);

        fireEvent.click(tag);

        expect(mockHandleChange).toHaveBeenCalledWith(mockLabel.name);
    });
});
