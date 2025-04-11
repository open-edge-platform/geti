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
