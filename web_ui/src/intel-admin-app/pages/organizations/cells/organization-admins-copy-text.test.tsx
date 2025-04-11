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

        expect(mockedCopy).toBeCalledWith(mockedAdmin.email, confirmationMessage);
    });
});
