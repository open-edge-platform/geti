// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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

    it('Learn section card should be visible', async () => {
        await render(<NoProjectArea openImportDatasetDialog={openImportDatasetDialog} />);

        expect(screen.getByText('Watch tutorials')).toBeInTheDocument();
    });

    it('Should display create button with creation menu', async () => {
        const usersService = createInMemoryUsersService();
        usersService.getActiveUser = async () => Promise.resolve(getMockedAdminUser());
        await render(<NoProjectArea openImportDatasetDialog={openImportDatasetDialog} />, {
            services: { usersService },
        });

        expect(await screen.findByRole('button', { name: 'Create new project' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Create project menu' })).toBeInTheDocument();
    });
});
