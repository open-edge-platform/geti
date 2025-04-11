// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { EditFullName } from './edit-full-name.component';

describe('EditFullName', () => {
    const mockedSetFirstName = jest.fn();
    const mockedSetLastName = jest.fn();
    const firstName = 'Name';
    const lastName = 'LastName';

    beforeEach(() => {
        render(
            <EditFullName
                firstName={firstName}
                lastName={lastName}
                setFirstName={mockedSetFirstName}
                setLastName={mockedSetLastName}
            />
        );
    });

    it('Check if full name is properly shown', () => {
        expect(screen.getByLabelText('First name')).toHaveValue(firstName);
        expect(screen.getByLabelText('Last name')).toHaveValue(lastName);
    });

    it('edit fullName calls callback function', async () => {
        const text = 'new';
        const firstNameElement = screen.getByLabelText('First name');
        const lastNameElement = screen.getByLabelText('Last name');

        await userEvent.click(firstNameElement);
        await userEvent.paste(text);
        expect(mockedSetFirstName).toHaveBeenCalledWith(`${firstName}${text}`);

        await userEvent.click(lastNameElement);
        await userEvent.paste(text);
        expect(mockedSetLastName).toHaveBeenCalledWith(`${lastName}${text}`);
    });
});
