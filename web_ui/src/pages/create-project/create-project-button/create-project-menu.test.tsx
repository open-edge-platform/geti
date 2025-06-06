// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { OverlayTriggerState } from '@react-stately/overlays';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DatasetImportToNewProjectProvider } from '../../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { ProjectsImportProvider } from '../../../providers/projects-import-provider/projects-import-provider.component';
import { applicationRender as render } from '../../../test-utils/application-provider-render';
import { CreateProjectMenu, CreateProjectMenuActions } from './create-project-menu.component';

jest.mock('../../../shared/components/has-permission/has-permission.component', () => ({
    useCheckPermission: jest.fn(() => true),
}));

const mockImportProject = jest.fn();
jest.mock('../../../providers/projects-import-provider/projects-import-provider.component', () => ({
    ProjectsImportProvider: ({ children }: { children: ReactNode }) => children,
    useProjectsImportProvider: () => ({
        importProject: mockImportProject,
        importItems: {},
        cancelImportProject: jest.fn(),
        removeImportProjectItemFromLS: jest.fn(),
        patchImportProjectItem: jest.fn(),
    }),
}));

const Wrapper = ({ children }: { children: ReactNode }) => {
    return (
        <DatasetImportToNewProjectProvider>
            <ProjectsImportProvider>{children}</ProjectsImportProvider>
        </DatasetImportToNewProjectProvider>
    );
};

describe('CreateProjectMenu', () => {
    const mockOpenImportDatasetDialog = {
        isOpen: false,
        open: jest.fn(),
        close: jest.fn(),
        toggle: jest.fn(),
        setOpen: jest.fn(),
    } as OverlayTriggerState;

    const renderCreateProjectMenu = async () => {
        await render(
            <Wrapper>
                <CreateProjectMenu openImportDatasetDialog={mockOpenImportDatasetDialog} />
            </Wrapper>
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
        mockImportProject.mockClear();
    });

    describe('Menu trigger and options', () => {
        it('should render the menu trigger button', async () => {
            await renderCreateProjectMenu();

            const menuButton = screen.getByRole('button', { name: 'Create project menu' });
            expect(menuButton).toBeInTheDocument();
        });

        it('should show menu options when trigger button is clicked', async () => {
            await renderCreateProjectMenu();

            const menuButton = screen.getByRole('button', { name: 'Create project menu' });
            fireEvent.click(menuButton);

            await waitFor(() => {
                expect(screen.getByRole('menuitem', { name: CreateProjectMenuActions.IMPORT_DATASET })).toBeVisible();
                expect(screen.getByRole('menuitem', { name: CreateProjectMenuActions.IMPORT_PROJECT })).toBeVisible();
            });
        });

        it('should open import project dialog when "Create from exported project" is clicked', async () => {
            await renderCreateProjectMenu();

            const menuButton = screen.getByRole('button', { name: 'Create project menu' });
            fireEvent.click(menuButton);

            const importProjectButton = await screen.findByRole('menuitem', {
                name: CreateProjectMenuActions.IMPORT_PROJECT,
            });
            fireEvent.click(importProjectButton);

            await waitFor(() => {
                expect(screen.getByRole('dialog')).toBeInTheDocument();
                expect(screen.getByRole('heading', { name: 'Import project' })).toBeVisible();
            });
        });
    });

    describe('Project name submission', () => {
        it('should pass empty project name to import panel when no name is entered', async () => {
            await renderCreateProjectMenu();

            const menuButton = screen.getByRole('button', { name: 'Create project menu' });
            fireEvent.click(menuButton);

            const importProjectButton = await screen.findByRole('menuitem', {
                name: CreateProjectMenuActions.IMPORT_PROJECT,
            });
            fireEvent.click(importProjectButton);

            await waitFor(() => {
                expect(screen.getByRole('dialog')).toBeInTheDocument();
                expect(screen.getByRole('heading', { name: 'Import project' })).toBeVisible();
            });

            const file = new File(['Project content'], 'test-project.zip', { type: 'application/x-zip' });
            const uploadFileElement = screen.getByLabelText('upload-media-input');

            await userEvent.upload(uploadFileElement, [file]);

            await waitFor(() => {
                expect(mockImportProject).toHaveBeenCalledWith(file, {
                    keepOriginalDates: false,
                    projectName: '',
                    skipSignatureVerification: true,
                });
            });
        });

        it('should pass entered project name to import panel when name is provided', async () => {
            await renderCreateProjectMenu();

            const menuButton = screen.getByRole('button', { name: 'Create project menu' });
            fireEvent.click(menuButton);

            const importProjectButton = await screen.findByRole('menuitem', {
                name: CreateProjectMenuActions.IMPORT_PROJECT,
            });
            fireEvent.click(importProjectButton);

            await waitFor(() => {
                expect(screen.getByRole('dialog')).toBeInTheDocument();
            });

            const projectNameInput = screen.getByRole('textbox', { name: /project name/i });
            const testProjectName = 'My Custom Project Name';
            await userEvent.type(projectNameInput, testProjectName);

            const file = new File(['Project content'], 'test-project.zip', { type: 'application/x-zip' });
            const uploadFileElement = screen.getByLabelText('upload-media-input');

            await userEvent.upload(uploadFileElement, [file]);

            await waitFor(() => {
                expect(mockImportProject).toHaveBeenCalledWith(file, {
                    keepOriginalDates: false,
                    projectName: testProjectName,
                    skipSignatureVerification: true,
                });
            });
        });

        it('should trim project name before passing to import panel', async () => {
            await renderCreateProjectMenu();

            const menuButton = screen.getByRole('button', { name: 'Create project menu' });
            fireEvent.click(menuButton);

            const importProjectButton = await screen.findByRole('menuitem', {
                name: CreateProjectMenuActions.IMPORT_PROJECT,
            });
            fireEvent.click(importProjectButton);

            await waitFor(() => {
                expect(screen.getByRole('dialog')).toBeInTheDocument();
            });

            const projectNameInput = screen.getByRole('textbox', { name: /project name/i });
            const projectNameWithSpaces = '  Project With Spaces  ';
            await userEvent.type(projectNameInput, projectNameWithSpaces);

            const file = new File(['Project content'], 'test-project.zip', { type: 'application/x-zip' });
            const uploadFileElement = screen.getByLabelText('upload-media-input');

            await userEvent.upload(uploadFileElement, [file]);

            await waitFor(() => {
                expect(mockImportProject).toHaveBeenCalledWith(file, {
                    keepOriginalDates: false,
                    projectName: projectNameWithSpaces.trim(),
                    skipSignatureVerification: true,
                });
            });
        });
    });
});
