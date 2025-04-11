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

import { OverlayTriggerState } from '@react-stately/overlays';
import { UseQueryResult } from '@tanstack/react-query';
import { fireEvent, screen } from '@testing-library/react';
import { AxiosError } from 'axios';

import { useStatus } from '../../../core/status/hooks/use-status.hook';
import { TOO_LOW_FREE_DISK_SPACE_IN_BYTES } from '../../../core/status/hooks/utils';
import { StatusProps } from '../../../core/status/status.interface';
import { createInMemoryUsersService } from '../../../core/users/services/in-memory-users-service';
import { DatasetImportToNewProjectProvider } from '../../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { ProjectsImportProvider } from '../../../providers/projects-import-provider/projects-import-provider.component';
import { applicationRender } from '../../../test-utils/application-provider-render';
import {
    getMockedContributorUser,
    getMockedOrganizationAdminUser,
} from '../../../test-utils/mocked-items-factory/mocked-users';
import { CreateProjectButton } from './create-project-button.component';
import { CreateProjectMenuActions } from './create-project-menu.component';

jest.mock('../../../core/status/hooks/use-status.hook', () => ({
    ...jest.requireActual('../../../core/status/hooks/use-status.hook'),
    useStatus: jest.fn(() => ({
        data: {
            freeSpace: 0,
            totalSpace: 0,
            runningJobs: 0,
        },
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

const renderApp = async (isAdmin = true) => {
    const usersService = createInMemoryUsersService();
    usersService.getActiveUser = async () => {
        if (isAdmin) {
            return getMockedOrganizationAdminUser();
        }

        return getMockedContributorUser();
    };

    await applicationRender(
        <DatasetImportToNewProjectProvider>
            <ProjectsImportProvider>
                <CreateProjectButton
                    buttonText={'Create project'}
                    handleOpenDialog={jest.fn()}
                    openImportDatasetDialog={{} as OverlayTriggerState}
                />
            </ProjectsImportProvider>
        </DatasetImportToNewProjectProvider>,
        { services: { usersService } }
    );
};

describe('CreateProjectButton', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('Should show "Create from dataset" and "Create from exported project"', async () => {
        jest.mocked(useStatus).mockReturnValue({
            data: { freeSpace: TOO_LOW_FREE_DISK_SPACE_IN_BYTES + 1, totalSpace: 10, runningJobs: 0 },
        } as UseQueryResult<StatusProps, AxiosError>);
        await renderApp();

        fireEvent.click(await screen.findByRole('button', { name: 'Create project menu' }));

        const importProjectButton = await screen.findByRole('menuitem', {
            name: CreateProjectMenuActions.IMPORT_PROJECT,
        });
        expect(importProjectButton).toBeInTheDocument();
        expect(importProjectButton).not.toHaveAttribute('aria-disabled');

        const importDatasetButton = screen.getByRole('menuitem', { name: CreateProjectMenuActions.IMPORT_DATASET });
        expect(importDatasetButton).toBeInTheDocument();
        expect(importDatasetButton).not.toHaveAttribute('aria-disabled');
    });

    it('low storage space disables import options', async () => {
        jest.mocked(useStatus).mockReturnValue({
            data: { freeSpace: TOO_LOW_FREE_DISK_SPACE_IN_BYTES - 1, totalSpace: 10, runningJobs: 0 },
        } as UseQueryResult<StatusProps, AxiosError>);

        await renderApp();

        fireEvent.click(screen.getByRole('button', { name: 'Create project menu' }));

        //TODO: Add it back once 'Export project' gets fixed
        /* expect(screen.getByRole('menuitem', { name: CreateProjectMenuActions.IMPORT_PROJECT })).toHaveAttribute(
            'aria-disabled',
            'true'
        ); */
        expect(screen.getByRole('menuitem', { name: CreateProjectMenuActions.IMPORT_DATASET })).toHaveAttribute(
            'aria-disabled',
            'true'
        );
    });

    it('Should show not "Create from exported project" to a contributor', async () => {
        jest.mocked(useStatus).mockReturnValue({
            data: { freeSpace: TOO_LOW_FREE_DISK_SPACE_IN_BYTES + 1, totalSpace: 10, runningJobs: 0 },
        } as UseQueryResult<StatusProps, AxiosError>);
        await renderApp(false);

        fireEvent.click(screen.getByRole('button', { name: 'Create project menu' }));

        const importProjectButton = screen.queryByRole('menuitem', { name: CreateProjectMenuActions.IMPORT_PROJECT });
        expect(importProjectButton).not.toBeInTheDocument();

        const importDatasetButton = screen.getByRole('menuitem', { name: CreateProjectMenuActions.IMPORT_DATASET });
        expect(importDatasetButton).toBeInTheDocument();
        expect(importDatasetButton).not.toHaveAttribute('aria-disabled');
    });
});
