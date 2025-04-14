// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider } from '@adobe/react-spectrum';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { PersonalAccessTokenExpirationDatepicker } from './personal-access-token-expiration-datepicker.component';

describe('PersonalAccessTokenExpirationDatepicker', () => {
    it('renders component', async () => {
        const mockSetDates = jest.fn();

        render(
            <Provider theme={defaultTheme}>
                <PersonalAccessTokenExpirationDatepicker setDate={mockSetDates} />
            </Provider>
        );

        const selectDateButton = screen.getByLabelText('Calendar');
        await userEvent.click(selectDateButton);

        const firstDate = screen.getByRole('button', { name: /First available date$/i });
        await userEvent.click(firstDate);

        expect(mockSetDates).toHaveBeenCalled();
    });
});
