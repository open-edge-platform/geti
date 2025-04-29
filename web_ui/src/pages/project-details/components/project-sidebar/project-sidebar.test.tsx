// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN, ProjectIdentifier } from '../../../../core/projects/core.interface';
import { PerformanceType } from '../../../../core/projects/task.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { getById, MORE_THAN_100_CHARS_NAME } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../providers/project-provider/project-provider.component';
import { ProjectSidebar } from './project-sidebar.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-123',
        workspaceId: 'workspace-123',
        organizationId: 'organization-123',
    }),
}));

const project = getMockedProject({ id: '123', domains: [DOMAIN.DETECTION] });

const render = async (ui: ReactElement) => {
    const result = providersRender(ui);

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return result;
};

describe('Project sidebar', () => {
    const projectIdentifier: ProjectIdentifier = getMockedProjectIdentifier({
        projectId: 'project-123',
        workspaceId: 'workspace-123',
    });

    it('Check if there is proper project title', async () => {
        const { container } = await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar project={project} />
            </ProjectProvider>
        );
        const projectTitle = getById(container, `project-name-${idMatchingFormat(project.name)}`);
        const pencilButton = screen.getByLabelText('Edit name of the project');
        const titleText = projectTitle?.textContent?.replace(pencilButton.textContent || '', '');

        expect(titleText).toBe(`Test project 1`);
    });

    it('Check if there is sidebar menu', async () => {
        const { container } = await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar project={project} />
            </ProjectProvider>
        );

        expect(getById(container, 'sidebar-menu-project-steps')).toBeInTheDocument();
    });

    it('Check if sidebar menu has proper options', async () => {
        const { container } = await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar project={project} />
            </ProjectProvider>
        );

        expect(getById(container, 'sidebar-menu-datasets')).toBeInTheDocument();
        expect(getById(container, 'sidebar-menu-models')).toBeInTheDocument();
        expect(getById(container, 'sidebar-menu-tests')).toBeInTheDocument();
        expect(getById(container, 'sidebar-menu-deployments')).toBeInTheDocument();
    });

    it('Check if name in edition is limited to 100', async () => {
        await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar project={project} />
            </ProjectProvider>
        );

        const editButton = screen.getByRole('button', { name: 'Edit name of the project' });

        fireEvent.click(editButton);

        const input = screen.getByRole('textbox', { name: 'Edit project name field' });

        await userEvent.clear(input);

        await userEvent.type(input, MORE_THAN_100_CHARS_NAME);

        expect(input).toHaveValue(MORE_THAN_100_CHARS_NAME.substring(0, 100));
    });
});

describe('project status', () => {
    const projectIdentifier = getMockedProjectIdentifier({ projectId: 'project-123', workspaceId: 'workspace-123' });

    it('Check project status and score in sidebar', async () => {
        await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar project={project} />
            </ProjectProvider>
        );

        // This score comes from in-memory-service
        expect(screen.getByText('Score: 77%')).toBeInTheDocument();
    });

    it('Returns "N/A" if score is null', async () => {
        await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar
                    project={getMockedProject({
                        performance: {
                            type: PerformanceType.DEFAULT,
                            score: null,
                            taskPerformances: [{ score: null, taskNodeId: 'task-id' }],
                        },
                    })}
                />
            </ProjectProvider>
        );

        expect(screen.getByText(/N\/A/i)).toBeInTheDocument();
    });

    it('Returns score value if score is not null', async () => {
        await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar
                    project={getMockedProject({
                        performance: {
                            type: PerformanceType.DEFAULT,
                            score: 0.15,
                            taskPerformances: [
                                { score: { value: 0.15, metricType: 'accuracy' }, taskNodeId: 'task-id' },
                            ],
                        },
                    })}
                />
            </ProjectProvider>
        );

        expect(screen.getByText(/15%/i)).toBeInTheDocument();
    });

    it('check if score is properly rounded - 0.768 should return 77', async () => {
        await render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <ProjectSidebar
                    project={getMockedProject({
                        performance: {
                            type: PerformanceType.DEFAULT,
                            score: 0.768,
                            taskPerformances: [
                                { score: { value: 0.768, metricType: 'accuracy' }, taskNodeId: 'task-id' },
                            ],
                        },
                    })}
                />
            </ProjectProvider>
        );

        expect(screen.getByText(/77%/i)).toBeInTheDocument();
    });
});
