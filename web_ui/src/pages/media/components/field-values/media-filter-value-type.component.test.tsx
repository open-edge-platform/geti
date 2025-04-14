// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
