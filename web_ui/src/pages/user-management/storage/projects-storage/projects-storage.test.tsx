// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getFileSize } from '@shared/utils';
import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { ProjectProps } from '../../../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedAdminUser, getMockedContributorUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectsStorage } from './projects-storage.component';

const mockedAdminUser = getMockedAdminUser();
const mockedContributorUser = getMockedContributorUser();

jest.mock('../../../../hooks/use-clear-indexeddb-storage/use-clear-indexeddb-storage.hook', () => {
    return {
        useClearProjectStorage: jest.fn(() => ({
            clearProjectStorage: jest.fn(),
        })),
    };
});

jest.mock('../../../../core/users/hook/use-users.hook', () => ({
    ...jest.requireActual('../../../../core/users/hook/use-users.hook'),
    useUsers: jest.fn(() => ({
        useActiveUser: jest.fn(() => ({ data: mockedAdminUser })),
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

const renderProjectsStorage = async ({ projects }: { projects: ProjectProps[] }) => {
    const projectService = createInMemoryProjectService();
    projectService.getProjects = jest.fn(async () =>
        Promise.resolve({
            projects,
            nextPage: null,
        })
    );

    render(<ProjectsStorage />, { services: { projectService } });

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return {
        projectService,
    };
};

describe('ProjectsStorage', () => {
    const projects = [
        getMockedProject({ id: '1', name: 'Olympic', storageInfo: { size: 1000 } }),
        getMockedProject({ id: '2', name: 'E-sport', storageInfo: { size: 2000 } }),
        getMockedProject({ id: '3', name: 'Games', storageInfo: { size: 3000 } }),
    ];

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('should allow user to switch between table view and graph view', async () => {
        await renderProjectsStorage({ projects });

        expect(screen.getByLabelText('Projects storage table')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /switch to graph view/i }));

        expect(screen.getByLabelText('Projects storage chart')).toBeInTheDocument();
    });

    it('should display project names, sizes and menu with delete option', async () => {
        await renderProjectsStorage({ projects });

        projects.forEach((project) => {
            expect(screen.getByText(project.name)).toBeInTheDocument();
            expect(screen.getByText(getFileSize(project.storageInfo.size))).toBeInTheDocument();
        });
    });

    it('should allow user to sort projects by name', async () => {
        const { projectService } = await renderProjectsStorage({ projects });

        fireEvent.click(screen.getByRole('columnheader', { name: /name/i }));

        await waitFor(() => {
            expect(projectService.getProjects).toHaveBeenLastCalledWith(
                expect.anything(),
                { sortBy: 'name', sortDir: 'asc' },
                null,
                expect.anything()
            );
        });
    });

    it('should allow admin user to delete the project', async () => {
        const [project] = projects;

        // @ts-expect-error We only care about data property
        jest.mocked(useUsers).mockReturnValue({ useActiveUser: () => ({ data: mockedAdminUser }) });

        const { projectService } = await renderProjectsStorage({ projects });
        const deleteProjectMock = jest.fn();
        projectService.deleteProject = deleteProjectMock;

        fireEvent.click(screen.getByTestId(`project-storage-action-${project.id}`));
        fireEvent.click(screen.getByRole('menuitem', { name: /delete/i }));

        expect(screen.getByRole('alertdialog')).toHaveTextContent(
            `Are you sure you want to delete project "${project.name}"?`
        );

        fireEvent.click(screen.getByRole('button', { name: /delete/i }));

        await waitFor(() => {
            expect(deleteProjectMock).toHaveBeenCalledWith(expect.objectContaining({ projectId: project.id }));
        });
    });

    it('should not allow contributor user to delete the project', async () => {
        const [project] = projects;
        // @ts-expect-error We only care about data property
        jest.mocked(useUsers).mockReturnValue({ useActiveUser: () => ({ data: mockedContributorUser }) });

        await renderProjectsStorage({ projects });

        expect(screen.queryByTestId(`project-storage-action-${project.id}`)).not.toBeInTheDocument();
    });

    it('should display a message when there are no projects', async () => {
        await renderProjectsStorage({ projects: [] });

        expect(await screen.findByRole('heading', { name: /you do not have any projects/i })).toBeInTheDocument();
    });
});
