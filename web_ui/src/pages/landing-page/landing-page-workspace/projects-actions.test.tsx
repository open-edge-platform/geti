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

import { useOverlayTriggerState } from '@react-stately/overlays';
import { screen } from '@testing-library/react';

import { ProjectSortingOptions } from '../../../core/projects/services/project-service.interface';
import { createInMemoryUsersService } from '../../../core/users/services/in-memory-users-service';
import { UsersService } from '../../../core/users/services/users-service.interface';
import { DatasetImportToNewProjectProvider } from '../../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { ProjectsImportProvider } from '../../../providers/projects-import-provider/projects-import-provider.component';
import { applicationRender as render } from '../../../test-utils/application-provider-render';
import { getMockedOrganizationAdminUser } from '../../../test-utils/mocked-items-factory/mocked-users';
import { ProjectsActions } from './projects-actions.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

describe('ProjectActions', () => {
    const App = ({ shouldShowProjectActions }: { shouldShowProjectActions: boolean }) => {
        const datasetImportDialogTrigger = useOverlayTriggerState({});

        return (
            <DatasetImportToNewProjectProvider>
                <ProjectsImportProvider>
                    <ProjectsActions
                        queryOptions={{ sortBy: ProjectSortingOptions.name, sortDir: 'asc' }}
                        setQueryOptions={jest.fn()}
                        shouldShowProjectActions={shouldShowProjectActions}
                        datasetImportDialogTrigger={datasetImportDialogTrigger}
                    />
                </ProjectsImportProvider>
            </DatasetImportToNewProjectProvider>
        );
    };

    const renderApp = async (hasProjects = true, usersService?: UsersService) => {
        await render(<App shouldShowProjectActions={hasProjects} />, { services: { usersService } });
    };

    it('Should not show search bar, sorting and create project button when there are no projects [create project button is placed in the create first project card]', async () => {
        await renderApp(false);

        expect(screen.queryByRole('searchbox')).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Create new project' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Sort' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Create project menu' })).not.toBeInTheDocument();
    });

    it('Should show search bar, sorting, create project button with creation menu', async () => {
        const usersService = createInMemoryUsersService();
        usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationAdminUser());

        await renderApp(true, usersService);

        expect(screen.getByRole('searchbox')).toBeInTheDocument();
        expect(await screen.findByRole('button', { name: 'Create new project' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Sort' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Create project menu' })).toBeInTheDocument();
    });
});
