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

import { screen, within } from '@testing-library/react';

import { createInMemoryUsersService } from '../../../core/users/services/in-memory-users-service';
import { getMockedAdminUser } from '../../../test-utils/mocked-items-factory/mocked-users';
import { projectListRender } from '../../../test-utils/projects-list-providers-render';
import { WorkspacesTabs } from './workspaces-tabs.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        workspaceId: 'workspace-id',
        organizationId: 'organization-123',
    }),
}));

describe('WorkspaceTabs', () => {
    it('only allows edit actions on a workspace for the selected workspace', async () => {
        const usersService = createInMemoryUsersService();
        usersService.getActiveUser = async () => {
            return getMockedAdminUser();
        };

        await projectListRender(<WorkspacesTabs />, {
            services: { usersService },
            featureFlags: { FEATURE_FLAG_WORKSPACE_ACTIONS: true },
        });

        const workspaces = await screen.findByRole('tablist', { name: 'Workspaces tabs' });
        expect(workspaces).toBeInTheDocument();

        const tabs = within(workspaces).getAllByRole('tab');
        expect(tabs).toHaveLength(2);

        const workspace1 = screen.getByRole('tab', { name: /Workspace 1/, selected: true });
        expect(workspace1).toBeInTheDocument();
        const workspace2 = screen.getByRole('tab', { name: /Workspace 2/, selected: false });
        expect(workspace2).toBeInTheDocument();

        expect(await within(workspace1).findByRole('button', { name: 'open menu' })).toBeInTheDocument();
        expect(within(workspace2).queryByRole('button', { name: 'open menu' })).not.toBeInTheDocument();
    });
});
