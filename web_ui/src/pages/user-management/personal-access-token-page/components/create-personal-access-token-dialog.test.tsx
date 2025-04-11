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

import { useOverlayTriggerState } from '@react-stately/overlays';
import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { CreatePersonalAccessTokenDialog } from './create-personal-access-token-dialog.component';

const App = () => {
    const createPersonalAccessTokenDialogState = useOverlayTriggerState({});

    return (
        <>
            <button onClick={createPersonalAccessTokenDialogState.open}>Open</button>
            <CreatePersonalAccessTokenDialog
                triggerState={createPersonalAccessTokenDialogState}
                userId={'2'}
                organizationId={'3'}
            />
        </>
    );
};
jest.mock('../../../../core/users/hook/use-users.hook', () => ({
    useUsers: jest.fn(() => ({
        useActiveUser: () => ({
            data: {},
            isPending: false,
        }),
    })),
}));

describe('CreatePersonalAccessTokenDialog', () => {
    const renderApp = async () => {
        const result = render(<App />);

        await userEvent.click(screen.getByRole('button', { name: 'Open' }));

        return result;
    };

    it('Open and close modal', async () => {
        await renderApp();

        expect(screen.getByText('Personal Access Token')).toBeInTheDocument();

        await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

        await waitFor(() => {
            expect(screen.queryByText('Personal Access Token')).not.toBeInTheDocument();
        });
    });

    it('Create is disabled with invalid dates', async () => {
        await renderApp();

        expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    });

    it('renders Copy options', async () => {
        await renderApp();

        expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();

        const nameTextField = screen.getByLabelText(/name/i);

        await userEvent.type(nameTextField, 'some api key name');
        expect(nameTextField).toHaveValue('some api key name');

        const selectDateButton = screen.getByLabelText('Calendar');

        await userEvent.click(selectDateButton);

        const firstDate = screen.getByRole('button', { name: /First available date$/i });

        await userEvent.click(firstDate);

        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();

        await userEvent.click(screen.getByRole('button', { name: 'Create' }));

        await waitFor(() => {
            expect(screen.getByLabelText('copy-api-key')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
        });
    });
});
