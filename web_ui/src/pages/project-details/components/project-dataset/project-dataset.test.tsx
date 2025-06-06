// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { API_URLS } from '@geti/core';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useLocation, useNavigate } from 'react-router-dom';

import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { ExportImportDatasetDialogProvider } from '../../../../features/dataset-export/components/export-import-dataset-dialog-provider.component';
import { DatasetImportToExistingProjectProvider } from '../../../../features/dataset-import/providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { DatasetProvider } from '../../../../providers/dataset-provider/dataset-provider.component';
import { MediaUploadProvider } from '../../../../providers/media-upload-provider/media-upload-provider.component';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { getById } from '../../../../test-utils/utils';
import { MediaProvider } from '../../../media/providers/media-provider.component';
import { ProjectDataset } from './project-dataset.component';

const mockWorkspaceId = 'workspace-id';
const mockProjectId = 'project-id';
const mockDatasetId = 'in-memory-dataset';
const mockOrganizationId = 'organization-id';
const mockedDatasetIdentifier = {
    organizationId: mockOrganizationId,
    workspaceId: mockWorkspaceId,
    projectId: mockProjectId,
    datasetId: mockDatasetId,
};

jest.mock('../../../annotator/hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: () => mockedDatasetIdentifier,
}));

jest.mock(
    '../../../../features/dataset-import/providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component',
    () => {
        return {
            ...jest.requireActual(
                '../../../../features/dataset-import/providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
            ),
            useDatasetImportToExistingProject: jest.fn(() => ({
                datasetImports: [],
                importDatasetToExistingProject: jest.fn(),
            })),
        };
    }
);

jest.mock('./hooks/open-notification-toast.hook', () => ({
    useOpenNotificationToast: jest.fn(),
}));

const mediaService = createInMemoryMediaService();

const renderApp = async () => {
    const { container } = await render(
        <MediaUploadProvider>
            <DatasetProvider>
                <MediaProvider>
                    <DatasetImportToExistingProjectProvider>
                        <ExportImportDatasetDialogProvider>
                            <ProjectDataset />
                        </ExportImportDatasetDialogProvider>
                    </DatasetImportToExistingProjectProvider>
                </MediaProvider>
            </DatasetProvider>
        </MediaUploadProvider>,
        { services: { mediaService } }
    );

    return { container };
};

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useLocation: jest.fn(),
    useNavigate: jest.fn(),
}));

describe('Project dataset', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should have one main tab: "Dataset"', async () => {
        jest.mocked(useLocation).mockImplementation(() => ({
            pathname: `${API_URLS.DATASET_URL(mockedDatasetIdentifier)}/media`,
            key: '',
            hash: '',
            search: '',
            state: '',
        }));

        await renderApp();

        expect(screen.getByLabelText('In memory dataset')).toBeVisible();
    });

    it('should has 2 sub tabs: "Media" and "Statistics"', async () => {
        jest.mocked(useLocation).mockImplementation(() => ({
            pathname: `${API_URLS.DATASET_URL(mockedDatasetIdentifier)}/media`,
            key: '',
            hash: '',
            search: '',
            state: '',
        }));

        await renderApp();

        expect(screen.getByRole('tab', { name: /Media/ })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /Statistics/ })).toBeInTheDocument();
    });

    it('should render media content component on "Media" tab', async () => {
        jest.mocked(useLocation).mockImplementation(() => ({
            pathname: `${API_URLS.DATASET_URL(mockedDatasetIdentifier)}/media`,
            key: '',
            hash: '',
            search: '',
            state: '',
        }));
        const { container } = await renderApp();

        await waitFor(() => {
            expect(getById(container, 'generic-content-id')).toBeInTheDocument();
        });
    });

    it('should render project annotations statistics component on "Statistics" tab click', async () => {
        jest.mocked(useLocation).mockImplementation(() => ({
            pathname: `${API_URLS.DATASET_URL(mockedDatasetIdentifier)}/statistics`,
            key: '',
            hash: '',
            search: '',
            state: '',
        }));
        const { container } = await renderApp();

        await waitFor(() => {
            expect(getById(container, 'project-annotations-statistics-id')).toBeInTheDocument();
        });
    });

    it('Should call navigate after tab clicking', async () => {
        const mockUseNavigate = jest.fn();

        jest.mocked(useNavigate).mockImplementation(() => mockUseNavigate);

        //@ts-expect-error we need to mock only pathname
        jest.mocked(useLocation).mockImplementation(() => ({
            pathname: `${API_URLS.DATASET_URL(mockedDatasetIdentifier)}/model`,
        }));

        await renderApp();

        const statisticsTab = screen.getByRole('tab', { name: /Statistics/ });

        // Wait for media items to be loaded so that the statistics tab becomes enabled
        await waitFor(() => {
            expect(statisticsTab).toBeEnabled();
        });

        fireEvent.click(statisticsTab);

        expect(mockUseNavigate).toHaveBeenCalledWith(
            '/organizations/organization-id/workspaces/workspace-id/projects/project-id/datasets/in-memory-dataset/statistics'
        );
    });

    it('Statistics should be disabled when media items are empty', async () => {
        jest.mocked(useLocation).mockImplementation(() => ({
            pathname: `${API_URLS.DATASET_URL(mockedDatasetIdentifier)}/media`,
            key: '',
            hash: '',
            search: '',
            state: '',
        }));

        mediaService.getAdvancedFilterMedia = jest.fn(() =>
            Promise.resolve({
                nextPage: undefined,
                media: [],
                totalImages: 0,
                totalMatchedImages: 0,
                totalMatchedVideoFrames: 0,
                totalMatchedVideos: 0,
                totalVideos: 0,
            })
        );

        await renderApp();

        expect(screen.getByRole('tab', { name: /Statistics/ })).toHaveAttribute('aria-disabled', 'true');
    });
});
