// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { defaultTheme, Provider } from '@adobe/react-spectrum';
import { fireEvent, render, screen } from '@testing-library/react';

import { MediaFilterValueDate } from './media-filter-value-date.component';

describe('MediaFilterValueDate', () => {
    const onSelectionChange = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders date and time without any errors', async () => {
        await render(
            <Provider theme={defaultTheme}>
                <MediaFilterValueDate value={''} onSelectionChange={onSelectionChange} />
            </Provider>
        );

        const selectDateButton = screen.getByLabelText('Calendar');
        fireEvent.click(selectDateButton);

        const today = screen.getByRole('button', { name: /Today/i });
        fireEvent.click(today);

        expect(onSelectionChange).toHaveBeenCalled();
    });

    it('sets a default date correctly', async () => {
        const mockDate = new Date(2020, 0, 1, 0, 0, 0).toISOString();

        await render(
            <Provider theme={defaultTheme}>
                <MediaFilterValueDate value={mockDate} onSelectionChange={onSelectionChange} />
            </Provider>
        );

        expect(screen.queryByText('Selected Date: January 1, 2020 at 12:00 AM', { exact: false })).toBeTruthy();
    });
});
