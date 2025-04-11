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

import { screen, waitFor } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { getById } from '../../../../test-utils/utils';
import { MediaProvider } from '../../../media/providers/media-provider.component';
import { ProjectAnnotationsStatistics } from './project-annotations-statistics.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: '123',
        organizationId: 'organization-123',
    }),
    useLocation: () => ({
        pathname:
            'localhost:3000/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/123/annotations',
    }),
}));

describe('Project annotations', () => {
    const renderApp = (project: ProjectProps) => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => project;

        return render(
            <MediaProvider>
                <ProjectAnnotationsStatistics />
            </MediaProvider>,
            { services: { projectService } }
        );
    };

    it('should render elements without task selection', async () => {
        const mockedProject = getMockedProject({
            tasks: [getMockedTask({ id: '1', domain: DOMAIN.DETECTION })],
        });
        const { container } = await renderApp(mockedProject);

        await waitFor(() => {
            expect(getById(container, 'media-images-id')).toBeInTheDocument();
        });

        expect(getById(container, 'task-selection-id')).not.toBeInTheDocument();
        expect(getById(container, 'media-images-count-id')).toBeInTheDocument();
        expect(getById(container, 'media-videos-id')).toBeInTheDocument();
        expect(getById(container, 'media-videos-count-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-images-count-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-images-progress-bar-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-videos-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-videos-count-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-frames-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-frame-count-id')).toBeInTheDocument();
        expect(screen.getByText('Object size distribution')).toBeInTheDocument();
    });

    it('hide Object size distribution for keypoint detection', async () => {
        const mockedProject = getMockedProject({
            tasks: [getMockedTask({ id: 'keypoint-task', domain: DOMAIN.KEYPOINT_DETECTION, title: 'Keypoint' })],
        });

        const { container } = await renderApp(mockedProject);

        await waitFor(() => {
            expect(getById(container, 'media-images-id')).toBeInTheDocument();
        });

        expect(screen.queryByText('Object size distribution')).not.toBeInTheDocument();
    });

    it('should render page with task selection for task chain project', async () => {
        const mockedProject = getMockedProject({
            tasks: [
                getMockedTask({ id: '1', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: '2', domain: DOMAIN.CLASSIFICATION }),
            ],
        });
        const { container } = await renderApp(mockedProject);

        await waitFor(() => {
            expect(getById(container, 'task-selection-id')).toBeInTheDocument();
        });
        expect(getById(container, 'media-images-id')).toBeInTheDocument();
        expect(getById(container, 'media-images-count-id')).toBeInTheDocument();
        expect(getById(container, 'media-videos-id')).toBeInTheDocument();
        expect(getById(container, 'media-videos-count-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-images-count-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-images-progress-bar-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-videos-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-videos-count-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-frames-id')).toBeInTheDocument();
        expect(getById(container, 'annotated-frame-count-id')).toBeInTheDocument();
        expect(screen.getByText('Object size distribution')).toBeInTheDocument();
    });
});
