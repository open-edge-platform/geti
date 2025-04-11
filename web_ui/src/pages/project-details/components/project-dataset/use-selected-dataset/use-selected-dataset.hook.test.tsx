// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
