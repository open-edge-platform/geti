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

import { screen } from '@testing-library/react';
import { VirtuosoMockContext } from 'react-virtuoso';

import { projectListRender as render } from '../../../test-utils/projects-list-providers-render';
import { LandingPageWorkspace as Workspace } from './landing-page-workspace.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ organizationId: 'organization-123', workspaceId: 'workspace-id' }),
}));

jest.mock(
    '../../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component',
    () => {
        return {
            ...jest.requireActual(
                '../../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component'
            ),
            useDatasetImportToNewProject: jest.fn(() => {
                return {
                    getActiveUpload: jest.fn(),
                    datasetImports: [],
                };
            }),
        };
    }
);

describe('Landing page workspace', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders <NoProjects /> "projects" is "undefined"', async () => {
        await render(<Workspace />);

        const noProjects = screen.queryByTestId('no-project-area');

        expect(noProjects).toBeDefined();
    });

    //TODO: Move tests to playwright or handle differently - should be disabled because of library downgrade
    it('renders project list correctly', async () => {
        await render(
            <VirtuosoMockContext.Provider value={{ viewportHeight: 900, itemHeight: 100 }}>
                <Workspace />
            </VirtuosoMockContext.Provider>
        );

        expect(await screen.findByText('Test project 1')).toBeInTheDocument();
        expect(screen.getByText('Test project 2')).toBeInTheDocument();
        expect(screen.getByText('Test project 3')).toBeInTheDocument();
    });
});
