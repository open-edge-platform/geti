// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
