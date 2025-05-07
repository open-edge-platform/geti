// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OverlayTriggerState } from '@react-stately/overlays';
import { screen } from '@testing-library/react';

import { createInMemoryUsersService } from '../../../../../core/users/services/in-memory-users-service';
import { getMockedAdminUser } from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { projectListRender as render } from '../../../../../test-utils/projects-list-providers-render';
import { getById } from '../../../../../test-utils/utils';
import { NoProjectArea } from './no-projects-area.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

const openImportDatasetDialog = {} as OverlayTriggerState;

describe('No projects area', () => {
    it('check if title and description are visible', async () => {
        const { container } = await render(<NoProjectArea openImportDatasetDialog={openImportDatasetDialog} />);

        const title = getById(container, 'no-projects-area-title');
        const description = getById(container, 'no-projects-area-description');

        expect(title).toBeInTheDocument();
        expect(description).toBeInTheDocument();
    });

    it('Check if there is proper message in the empty workspace area', async () => {
        const DESCRIPTION = 'Create new project to leverage AI to automate your Computer Vision task';

        await render(<NoProjectArea openImportDatasetDialog={openImportDatasetDialog} />);

        expect(screen.getByText(DESCRIPTION)).toBeInTheDocument();
    });

    it('Should display create button with creation menu', async () => {
        const usersService = createInMemoryUsersService();
        usersService.getActiveUser = async () => Promise.resolve(getMockedAdminUser());
        await render(<NoProjectArea openImportDatasetDialog={openImportDatasetDialog} />, {
            services: { usersService },
        });

        expect(await screen.findByRole('button', { name: 'Create new project' })).toBeInTheDocument();
    });
});
