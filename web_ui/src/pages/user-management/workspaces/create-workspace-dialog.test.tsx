// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { applicationRender as render } from '../../../test-utils/application-provider-render';
import { CreateWorkspaceDialog } from './create-workspace-dialog.component';

describe('CreateWorkspaceDialog', () => {
    it('Check dialog elements', async () => {
        await render(<CreateWorkspaceDialog />);

        await userEvent.click(screen.getByRole('button', { name: 'Create new workspace' }));
        expect(screen.getByRole('dialog')).toBeInTheDocument();

        expect(screen.getByText('Create workspace')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();

        await userEvent.type(screen.getByLabelText('New workspace new'), 'New workspace');
        expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled();
    });
});
