// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../../core/projects/services/project-service.interface';
import { getMockedDataset } from '../../../../../test-utils/mocked-items-factory/mocked-datasets';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { renderHookWithProviders } from '../../../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { useSelectedDataset } from './use-selected-dataset.hook';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        datasetId: 'some-id',
    }),
}));

const renderSelectedDatasetHook = (params: { projectService: ProjectService }) => {
    return renderHookWithProviders(useSelectedDataset, {
        wrapper: ({ children }) => (
            <ProjectProvider
                projectIdentifier={{
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                    organizationId: 'organization-id',
                }}
            >
                {children}
            </ProjectProvider>
        ),
        providerProps: { projectService: params.projectService },
    });
};

const projectService = createInMemoryProjectService();

describe('useSelectedDataset', () => {
    it('returns the first dataset if there is none matching the url param', async () => {
        projectService.getProject = async () =>
            getMockedProject({
                datasets: [
                    getMockedDataset({ id: 'first-dataset-id' }),
                    getMockedDataset({ id: 'some-id-that-is-not-in-the-url' }),
                ],
            });
        const { result } = renderSelectedDatasetHook({ projectService });

        await waitFor(() => {
            expect(result.current?.id).toEqual('first-dataset-id');
        });
    });

    it('returns the correct dataset based on the url params', async () => {
        projectService.getProject = async () => getMockedProject({ datasets: [getMockedDataset({ id: 'some-id' })] });
        const { result } = renderSelectedDatasetHook({ projectService });

        await waitFor(() => {
            expect(result.current.id).toEqual('some-id');
        });
    });
});
