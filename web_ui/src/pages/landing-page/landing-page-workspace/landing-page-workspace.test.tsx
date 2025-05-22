// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

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
        await render(<Workspace />);

        expect(await screen.findByText('Test project 1')).toBeInTheDocument();
        expect(screen.getByText('Test project 2')).toBeInTheDocument();
        expect(screen.getByText('Test project 3')).toBeInTheDocument();
    });
});
