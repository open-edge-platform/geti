// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { OrganizationAdminsCopyText } from './organization-admins-copy-text.component';

const mockedCopy = jest.fn();

jest.mock('../../../../hooks/use-clipboard/use-clipboard.hook', () => ({
    useClipboard: () => ({ copy: mockedCopy }),
}));

const mockedAdmin = {
    firstName: 'Jane',
    lastName: 'Doe',
    email: 'jane@doe.com',
};

describe('OrganizationAdminsCopyText', () => {
    it('Check copying of admin email', async () => {
        const confirmationMessage = 'Email copied successfully';
        const testId = 'copy-email-${mockedAdmin.email}';

        render(
            <OrganizationAdminsCopyText
                text={mockedAdmin.email}
                confirmationMessage={confirmationMessage}
                aria-label={'Copy email'}
                data-testid={testId}
            />
        );

        expect(screen.getByTestId(testId)).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Copy email' }));

        expect(mockedCopy).toHaveBeenCalledWith(mockedAdmin.email, confirmationMessage);
    });
});
