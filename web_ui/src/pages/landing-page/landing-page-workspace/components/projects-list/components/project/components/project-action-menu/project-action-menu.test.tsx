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

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { useUsers } from '../../../../../../../../../core/users/hook/use-users.hook';
import { getMockedProject } from '../../../../../../../../../test-utils/mocked-items-factory/mocked-project';
import {
    getMockedOrganizationAdminUser,
    getMockedOrganizationContributorUser,
} from '../../../../../../../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../../../../../../../test-utils/required-providers-render';
import { ProjectActionMenu } from './project-action-menu.component';

const mockedOrganizationAndWorkspaceAdmin = getMockedOrganizationAdminUser();

const mockedContributorUser = getMockedOrganizationContributorUser();

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

jest.mock('../../../../../../../../../core/users/hook/use-users.hook', () => ({
    ...jest.requireActual('../../../../../../../../../core/users/hook/use-users.hook'),
    useUsers: jest.fn(() => ({
        useActiveUser: jest.fn(() => ({ data: mockedOrganizationAndWorkspaceAdmin })),
    })),
}));

const renderProjectActionMenu = async () => {
    render(
        <ProjectActionMenu
            project={getMockedProject({ id: 'project-id' })}
            isExporting={false}
            onExportProject={jest.fn()}
            onDeleteProject={jest.fn()}
        />
    );

    fireEvent.click(screen.getByRole('button', { name: 'action menu' }));
};

describe('ProjectActionMenu', () => {
    it('should have "Delete", "Export" and "Rename" actions', async () => {
        jest.mocked(useUsers).mockReturnValue({
            // @ts-expect-error We only care about data property
            useActiveUser: () => ({ data: mockedOrganizationAndWorkspaceAdmin }),
        });

        await renderProjectActionMenu();

        await waitFor(() => {
            ['Delete', 'Export', 'Rename'].forEach((item) => {
                expect(screen.getByRole('menuitem', { name: item })).toBeVisible();
            });
        });
    });

    it('should have only "Export" action', async () => {
        // @ts-expect-error We only care about data property
        jest.mocked(useUsers).mockReturnValue({ useActiveUser: () => ({ data: mockedContributorUser }) });

        await renderProjectActionMenu();

        expect(screen.getByRole('menuitem', { name: 'Export' })).toBeVisible();

        ['Delete', 'Rename'].forEach((item) => {
            expect(screen.queryByRole('menuitem', { name: item })).not.toBeInTheDocument();
        });
    });

    it('should open a dialog to edit project name when clicking on "Rename" action', async () => {
        jest.mocked(useUsers).mockReturnValue({
            // @ts-expect-error We only care about data property
            useActiveUser: () => ({ data: mockedOrganizationAndWorkspaceAdmin }),
        });

        await renderProjectActionMenu();

        fireEvent.click(screen.getByRole('menuitem', { name: 'Rename' }));

        expect(screen.getByRole('dialog')).toBeVisible();
        expect(screen.getByRole('heading', { name: 'Edit project name' })).toBeVisible();
    });

    it('should show alert dialog when clicking "Delete"', async () => {
        jest.mocked(useUsers).mockReturnValue({
            // @ts-expect-error We only care about data property
            useActiveUser: () => ({ data: mockedOrganizationAndWorkspaceAdmin }),
        });

        await renderProjectActionMenu();

        fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));

        expect(screen.getByRole('alertdialog')).toBeVisible();
        expect(screen.getByRole('heading', { name: 'Delete' })).toBeVisible();
    });
});
