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
