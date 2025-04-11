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

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { DOMAIN } from '../../../core/projects/core.interface';
import { ProjectProps } from '../../../core/projects/project.interface';
import { REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE } from '../../../pages/create-project/components/utils';
import { ProjectsImportProvider } from '../../../providers/projects-import-provider/projects-import-provider.component';
import { getMockedProject } from '../../../test-utils/mocked-items-factory/mocked-project';
import { providersRender } from '../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../test-utils/utils';
import { ProjectNameDomain } from './project-name-domain.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const render = (project: ProjectProps) => {
    providersRender(
        <ProjectsImportProvider>
            <ProjectNameDomain project={project} />
        </ProjectsImportProvider>
    );
};

describe('ProjectNameDomain', () => {
    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('Anomaly project is rendered as "Anomaly Classification"', async () => {
        const mockedProject = getMockedProject({
            id: '1111',
            name: 'Anomaly classification',
            domains: [DOMAIN.ANOMALY_CLASSIFICATION],
        });

        render(mockedProject);
        await waitFor(() => {
            expect(screen.getByText('Anomaly classification')).toBeInTheDocument();
        });
    });

    it('Project name cannot be edited to name with only space character', async () => {
        const mockedProject = getMockedProject({
            id: '1111',
            domains: [DOMAIN.SEGMENTATION],
        });

        const textInputValue = 'Edit name of the project';

        render(mockedProject);

        fireEvent.click(screen.getByRole('button', { name: textInputValue }));

        const input = await screen.findByLabelText('Edit project name field');
        fireEvent.change(input, { target: { value: '' } });
        fireEvent.blur(input);

        expect(screen.getByText(REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE)).toBeInTheDocument();
    });

    it('Entire project name should be visible in the tooltip', async () => {
        jest.useFakeTimers();
        const projectName = 'Mocked name of the project with a really, really, really long name that cannot be shorter';
        const mockedProject = getMockedProject({
            id: '1111',
            name: projectName,
            domains: [DOMAIN.SEGMENTATION],
        });

        render(mockedProject);

        await checkTooltip(screen.getByTestId('project-name-id'), projectName);
    });
});
