// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider } from '@geti/ui';
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
