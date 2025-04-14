// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';

import { mockedProjectContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { ThemeProvider } from '../../../../../theme/theme-provider.component';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { ExportImportDatasetButtons } from './export-import-dataset-buttons.component';
import { ExportImportDatasetDialogProvider } from './export-import-dataset-dialog-provider.component';

jest.mock('../../../providers/project-provider/project-provider.component', () => ({
    useProject: jest.fn(),
}));

describe('ExportImportDatasetButtons', () => {
    it('should display "Import dataset" button', () => {
        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ isTaskChainProject: false }));

        const { getImportDatasetButton } = renderComponent(false);

        expect(getImportDatasetButton()).toBeInTheDocument();
    });

    it('should display "Export dataset" button', () => {
        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ isTaskChainProject: true }));

        const { getExportDatasetButton } = renderComponent(true);

        expect(getExportDatasetButton()).toBeInTheDocument();
    });

    it('should display export and import in the menu', () => {
        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ isTaskChainProject: false }));

        const { openExportImportDatasetMenu, getImportDatasetMenuItem, getExportDatasetMenuItem } =
            renderComponent(true);

        openExportImportDatasetMenu();

        expect(getExportDatasetMenuItem()).toBeInTheDocument();
        expect(getImportDatasetMenuItem()).toBeInTheDocument();
    });

    it('should not display any button', () => {
        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ isTaskChainProject: true }));

        const { getExportDatasetButton, getImportDatasetButton, getExportImportDatasetMenuButton } =
            renderComponent(false);

        expect(getExportDatasetButton()).not.toBeInTheDocument();
        expect(getImportDatasetButton()).not.toBeInTheDocument();
        expect(getExportImportDatasetMenuButton()).not.toBeInTheDocument();
    });
});

const renderComponent = (hasMediaItems: boolean) => {
    render(
        <ThemeProvider>
            <ExportImportDatasetDialogProvider>
                <ExportImportDatasetButtons hasMediaItems={hasMediaItems} />
            </ExportImportDatasetDialogProvider>
        </ThemeProvider>
    );

    const getImportDatasetButton = () => screen.queryByRole('button', { name: /import dataset/i });

    const getExportDatasetButton = () => screen.queryByRole('button', { name: /export dataset/i });

    const getExportImportDatasetMenuButton = () =>
        screen.queryByRole('button', {
            name: /export or import dataset/i,
        });

    const openExportImportDatasetMenu = () => {
        const button = getExportImportDatasetMenuButton();
        button !== null && fireEvent.click(button);
    };

    const getExportDatasetMenuItem = () =>
        screen.getByRole('menuitem', {
            name: /export dataset/i,
        });

    const getImportDatasetMenuItem = () =>
        screen.getByRole('menuitem', {
            name: /import dataset/i,
        });

    return {
        getExportDatasetMenuItem,
        getImportDatasetMenuItem,
        getExportDatasetButton,
        getImportDatasetButton,
        getExportImportDatasetMenuButton,
        openExportImportDatasetMenu,
    };
};
