// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen, waitFor } from '@testing-library/react';

import { JobState, JobStepState } from '../../../core/jobs/jobs.const';
import { ExportFormats } from '../../../core/projects/dataset.interface';
import { createInMemoryProjectService } from '../../../core/projects/services/in-memory-project-service';
import { getMockedDatasetIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedDatasetExportJob } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { ExportDatasetStatusJob } from './export-dataset-status-job.component';

const mockedProjectService = createInMemoryProjectService();

const mockDatasetIdentifier = getMockedDatasetIdentifier({
    organizationId: '1234',
    workspaceId: '4321',
    projectId: '2341',
    datasetId: '3124',
});
const mockLocalStorage = {
    datasetId: '123',
    exportFormat: ExportFormats.YOLO,
    isPrepareDone: false,
    exportDatasetId: '321',
    datasetName: 'testDataset',
};

describe('ExportDatasetStatusJob', () => {
    const renderApp = () => {
        const mockOnPrepareDone = jest.fn();
        const mockOnCloseStatus = jest.fn();

        const component = render(
            <RequiredProviders projectService={mockedProjectService}>
                <ExportDatasetStatusJob
                    onCloseStatus={mockOnCloseStatus}
                    datasetIdentifier={mockDatasetIdentifier}
                    localStorageData={mockLocalStorage}
                    onPrepareDone={mockOnPrepareDone}
                />
            </RequiredProviders>
        );

        return { mockOnCloseStatus, mockOnPrepareDone, component };
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it("displays job's progress metadata", async () => {
        mockedProjectService.exportDatasetStatusJob = async () =>
            getMockedDatasetExportJob({
                state: JobState.RUNNING,
                steps: [
                    {
                        message: 'Exporting a dataset to datumaro format',
                        index: 1,
                        progress: 92.41860465116278,
                        state: JobStepState.RUNNING,
                        stepName: 'Create export dataset',
                        duration: undefined,
                        warning: undefined,
                    },
                ],
            });

        renderApp();

        expect(await screen.findByText('Export dataset "testDataset" - YOLO format')).toBeVisible();
        expect(screen.getByText('Create export dataset: Exporting a dataset to datumaro format')).toBeVisible();
        expect(screen.getByTestId('123-export-dataset-progress-progress')).toHaveTextContent('92%');
    });

    it('job is done', async () => {
        const downloadUrl = '/test-url';

        mockedProjectService.exportDatasetStatusJob = async () =>
            getMockedDatasetExportJob({
                state: JobState.FINISHED,
                metadata: { downloadUrl, project: { id: 'some-id', name: 'some-name' } },
            });

        const { mockOnCloseStatus, mockOnPrepareDone } = renderApp();

        expect(await screen.findByText(`Dataset "${mockLocalStorage.datasetName}" is ready to download`)).toBeVisible();
        expect(mockOnCloseStatus).not.toHaveBeenCalled();

        const { datasetId, datasetName, exportDatasetId, exportFormat } = mockLocalStorage;
        expect(mockOnPrepareDone).toHaveBeenCalledWith({
            downloadUrl,
            datasetId,
            datasetName,
            exportDatasetId,
            exportFormat,
            isPrepareDone: false,
        });
    });

    it('job is done, download url does not have the initial slash', async () => {
        const downloadUrl = 'test-url';

        mockedProjectService.exportDatasetStatusJob = async () =>
            getMockedDatasetExportJob({
                state: JobState.FINISHED,
                metadata: { downloadUrl, project: { id: 'some-id', name: 'some-name' } },
            });

        const { mockOnCloseStatus, mockOnPrepareDone } = renderApp();

        expect(await screen.findByText(`Dataset "${mockLocalStorage.datasetName}" is ready to download`)).toBeVisible();
        expect(mockOnPrepareDone).toHaveBeenCalledWith(expect.objectContaining({ downloadUrl: `/${downloadUrl}` }));
        expect(mockOnCloseStatus).not.toHaveBeenCalled();
    });

    it('job failed', async () => {
        mockedProjectService.exportDatasetStatusJob = async () => getMockedDatasetExportJob({ state: JobState.FAILED });

        const { mockOnCloseStatus, mockOnPrepareDone } = renderApp();

        expect(await screen.findByText(`Something went wrong. Please try again`)).toBeVisible();
        expect(mockOnCloseStatus).toHaveBeenCalledWith(mockLocalStorage.datasetId);
        expect(mockOnPrepareDone).not.toHaveBeenCalled();
    });

    it('job cancelled', async () => {
        mockedProjectService.exportDatasetStatusJob = async () =>
            getMockedDatasetExportJob({
                state: JobState.CANCELLED,
                metadata: { project: { id: 'some-id', name: 'some-name' } },
            });
        const { mockOnCloseStatus, mockOnPrepareDone } = renderApp();

        await waitFor(() => {
            expect(mockOnCloseStatus).toHaveBeenCalledWith(mockLocalStorage.datasetId);
            expect(mockOnPrepareDone).not.toHaveBeenCalled();
        });
    });
});
