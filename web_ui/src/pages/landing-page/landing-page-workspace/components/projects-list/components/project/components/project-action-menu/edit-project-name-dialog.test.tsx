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

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { ProjectProps } from '../../../../../../../../../core/projects/project.interface';
import { getMockedProject } from '../../../../../../../../../test-utils/mocked-items-factory/mocked-project';
import { providersRender as render } from '../../../../../../../../../test-utils/required-providers-render';
import { EditProjectNameDialog } from './edit-project-name-dialog.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const mockedProject = getMockedProject({});

const renderEditProjectNameDialog = async (project: ProjectProps = mockedProject) => {
    render(<EditProjectNameDialog onClose={jest.fn()} isOpen project={project} />);
};

const getEditProjectNameField = () => screen.getByRole('textbox', { name: /edit project name field/i });
const getSaveProjectNameButton = () => screen.getByRole('button', { name: /save/i });

describe('EditProjectNameDialog', () => {
    it('edit button should be disabled when new project name is empty', async () => {
        await renderEditProjectNameDialog();

        await userEvent.clear(getEditProjectNameField());

        expect(getEditProjectNameField()).toHaveValue('');
        expect(getSaveProjectNameButton()).toBeDisabled();
    });

    it('edit button should be disabled when new project name is the same as the old one', async () => {
        const projectName = 'test-project-name';
        await renderEditProjectNameDialog(getMockedProject({ name: projectName }));

        expect(getEditProjectNameField()).toHaveValue(projectName);
        expect(getSaveProjectNameButton()).toBeDisabled();
    });

    it('edit button should be enabled when new project name is different from the old one', async () => {
        const projectName = 'test-project-name';
        await renderEditProjectNameDialog(getMockedProject({ name: projectName }));

        await userEvent.clear(getEditProjectNameField());
        await userEvent.type(getEditProjectNameField(), 'new-project-name');

        expect(getSaveProjectNameButton()).toBeEnabled();
    });
});
