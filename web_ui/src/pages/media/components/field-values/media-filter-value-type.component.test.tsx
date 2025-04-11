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

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { MEDIA_TYPE_OPTIONS } from '../../utils';
import { MediaFilterValueType } from './media-filter-value-type.component';

describe('MediaFilterValueType', () => {
    const mockOnSelectionChange = jest.fn();

    it('opens dropdown menu', async () => {
        render(<MediaFilterValueType value={1} onSelectionChange={mockOnSelectionChange} />);

        fireEvent.click(screen.getByLabelText('media-filter-media-type'));
        const options = screen.getAllByRole('option');

        expect(options).toHaveLength(MEDIA_TYPE_OPTIONS.length);
    });

    it('has correct types and triggers callback', async () => {
        render(<MediaFilterValueType value={1} onSelectionChange={mockOnSelectionChange} />);

        fireEvent.click(screen.getByLabelText('media-filter-media-type'));

        expect(screen.getByRole('option', { name: 'Image' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Video' })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('option', { name: 'Image' }));

        expect(mockOnSelectionChange).toHaveBeenCalledWith('IMAGE');
    });
});
