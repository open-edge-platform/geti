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
